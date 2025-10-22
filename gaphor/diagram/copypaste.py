"""Copy and deep/shallow paste elements in a model or between models.

The `copy_full()` function will return all values serialized, either as string
values or reference id's.

The `paste_link()` function will resolve those values and place instances of
them on the diagram using the same defining element.
The `paste_full()` function is similar, but it creates new defining elements
for the elements being pasted.

The `copy()` dispatch function is an iterator that returns a copy of the element
and optionally any related elements. E.g. a Presentation element is likely
to also create a copy of its subject.

The `paste()` dispatch function works in two parts. First it creates the element
and yields it. On the next invocation it will populate the element and perform
complete the model loading.

`copy()` and `paste()` use `Base`'s `save()` and `load()` methods.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Iterator
from functools import singledispatch
from typing import NamedTuple

from gaphor.core.modeling import Base, Diagram, Id, Presentation
from gaphor.core.modeling.collection import collection
from gaphor.diagram.group import owner, owns

Opaque = object


class CopyData(NamedTuple):
    elements: dict[Id, Opaque]
    diagram_refs: set[Id]


def copy_full(
    items: Collection[Base], lookup: Callable[[Id], Base | None] | None = None
) -> CopyData:
    """Copy items, including owned elements."""

    elements = {ref: data for item in items for ref, data in copy(item)}
    diagram_refs = {item.diagram.id for item in items if isinstance(item, Presentation)}

    if not lookup:
        return CopyData(elements=elements, diagram_refs=diagram_refs)

    def copy_owned(e: Base):
        for o in owns(e):
            if owner(o) is e:
                for ref, data in copy(o):
                    if ref not in elements:
                        elements[ref] = data
                        copy_owned(o)

    for ref in list(elements.keys()):
        if element := lookup(ref):
            copy_owned(element)

    return CopyData(elements=elements, diagram_refs=diagram_refs)


def paste_link(copy_data: Opaque, diagram: Diagram) -> set[Presentation]:
    return _paste(copy_data, diagram, full=False)


def paste_full(copy_data: Opaque, diagram: Diagram) -> set[Presentation]:
    return _paste(copy_data, diagram, full=True)


@singledispatch
def copy(obj: Base | Iterable) -> Iterator[tuple[Id, Opaque]]:
    """Create a copy of an element (or list of elements).

    The returned type should be distinct, so the `paste()` function can
    properly dispatch.
    """
    raise ValueError(f"No copier for {obj}")


@singledispatch
def paste(
    copy_data: Opaque, diagram: Diagram, lookup: Callable[[Id], Base | None]
) -> Iterator[Base]:
    """Paste previously copied data.

    Based on the data type created in the `copy()` function, try to
    duplicate the copied elements.
    """
    raise ValueError(f"No paster for {copy_data}")


def serialize(value):
    if isinstance(value, Base):
        return ("r", value.id)
    elif isinstance(value, collection):
        return ("c", [serialize(v) for v in value])
    else:
        if isinstance(value, bool):
            value = int(value)
        return ("v", str(value))


def deserialize(ser, lookup):
    vtype, value = ser
    if vtype == "r":
        if e := lookup(value):
            yield e
    elif vtype == "c":
        for v in value:
            yield from deserialize(v, lookup)
    elif vtype == "v":
        yield value


def copy_base_data(
    element: Base, blacklist: list[str] | None = None
) -> dict[str, tuple[str, str]]:
    data = {}

    def save_func(name, value):
        if blacklist is None or name not in blacklist:
            data[name] = serialize(value)

    element.save(save_func)
    return data


class BaseCopy(NamedTuple):
    cls: type[Base]
    id: Id
    data: dict[str, tuple[str, str]]


def copy_element(element: Base, blacklist: list[str] | None = None) -> BaseCopy:
    data = copy_base_data(
        element, blacklist + ["presentation"] if blacklist else ["presentation"]
    )
    return BaseCopy(cls=element.__class__, id=element.id, data=data)


@copy.register
def _copy_element(element: Base) -> Iterator[tuple[Id, BaseCopy]]:
    yield element.id, copy_element(element)


@copy.register
def copy_diagram(element: Diagram) -> Iterator[tuple[Id, Opaque]]:
    yield element.id, copy_element(element, blacklist=["ownedPresentation"])
    for presentation in element.ownedPresentation:
        if presentation.subject is element:
            continue
        yield from copy(presentation)


def paste_element(
    copy_data: BaseCopy,
    diagram,
    lookup,
    filter: Callable[[str, str | int | Base], bool] | None = None,
) -> Iterator[Base]:
    cls, _id, data = copy_data
    element = diagram.model.create(cls)
    yield element
    for name, ser in data.items():
        for value in deserialize(ser, lookup):
            if not filter or filter(name, value):
                element.load(name, value)
    element.postload()


paste.register(BaseCopy, paste_element)


class PresentationCopy(NamedTuple):
    cls: type[Base]
    data: dict[str, tuple[str, str]]
    diagram: Id
    parent: Id | None


def copy_presentation(item: Presentation) -> PresentationCopy:
    assert item.diagram

    parent = item.parent
    return PresentationCopy(
        cls=item.__class__,
        data=copy_base_data(item, blacklist=["diagram", "parent", "children"]),
        diagram=item.diagram.id,
        parent=parent.id if parent else None,
    )


@copy.register
def _copy_presentation(item: Presentation) -> Iterator[tuple[Id, object]]:
    yield item.id, copy_presentation(item)
    if item.subject:
        yield from copy(item.subject)


@paste.register
def _paste_presentation(copy_data: PresentationCopy, _diagram, lookup):
    cls, data, diagram_ref, parent = copy_data
    diagram = lookup(diagram_ref)
    item = diagram.create(cls)
    yield item
    if parent:
        if p := lookup(parent):
            item.parent = p

    for name, ser in data.items():
        for value in deserialize(ser, lookup):
            item.load(name, value)
    diagram.update({item})


def _paste(copy_data: Opaque, diagram: Diagram, full: bool) -> set[Presentation]:
    assert isinstance(copy_data, CopyData)

    model = diagram.model

    # Map the original diagram ids to our new target diagram
    new_elements: dict[Id, Base] = dict.fromkeys(copy_data.diagram_refs, diagram)

    def element_lookup(ref: Id):
        if ref in new_elements:
            return new_elements[ref]

        looked_up = model.lookup(ref)
        if not full and looked_up and not isinstance(looked_up, Presentation):
            return looked_up

        if ref in copy_data.elements:
            paster = paste(copy_data.elements[ref], diagram, element_lookup)
            new_elements[ref] = next(paster)
            next(paster, None)
            return new_elements[ref]

        if full and looked_up and not isinstance(looked_up, Presentation):
            return looked_up

        if looked_up := diagram.lookup(ref):
            return looked_up

    for old_id in copy_data.elements.keys():
        if old_id in new_elements:
            continue
        element_lookup(old_id)

    for element in new_elements.values():
        assert element
        element.postload()

    return {
        e
        for e in new_elements.values()
        if isinstance(e, Presentation) and e.diagram is diagram
    }
