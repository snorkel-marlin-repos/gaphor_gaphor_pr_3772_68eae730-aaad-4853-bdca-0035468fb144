from __future__ import annotations

from collections.abc import Iterable
from operator import setitem

from gaphor.core.modeling import (
    Base,
    ElementChange,
    ElementFactory,
    Presentation,
    RefChange,
    StyleSheet,
    UnlimitedNatural,
    ValueChange,
)
from gaphor.core.modeling.collection import collection


class UnmatchableModel(Exception):
    def __init__(self, ancestor, incoming):
        super().__init__(f"Incompatible types {ancestor} != {incoming}")
        self.ancestor = ancestor
        self.incoming = incoming


def compare(
    current: ElementFactory, ancestor: ElementFactory, incoming: ElementFactory
) -> Iterable[ElementChange | ValueChange | RefChange]:
    """Compare two models.

    Changes are recorded in the current model as `PendingChange` objects
    (`ElementChange`, `ValueChange`, `RefChange`).

    Returns an iterable of the added change objects.
    """
    ancestor_keys = set(ancestor.keys())
    incoming_keys = set(incoming.keys())

    ancestor_style_sheet = None
    incoming_style_sheet = None

    def create(type, **kwargs):
        e = current.create(type)
        for name, value in kwargs.items():
            setattr(e, name, None if value is None else str(value))
        return e

    for key in ancestor_keys.difference(incoming_keys):
        e = ancestor[key]
        if isinstance(e, StyleSheet):
            ancestor_style_sheet = e
        else:
            yield create(
                ElementChange,
                op="remove",
                element_name=type(e).__name__,
                modeling_language=type(e).__modeling_language__,
                element_id=key,
            )

    for key in incoming_keys.difference(ancestor_keys):
        e = incoming[key]
        if isinstance(e, StyleSheet):
            incoming_style_sheet = e
        else:
            yield create(
                ElementChange,
                op="add",
                element_name=type(e).__name__,
                modeling_language=type(e).__modeling_language__,
                element_id=key,
                diagram_id=e.diagram.id if isinstance(e, Presentation) else None,
            )
            yield from updated_properties(None, e, create)

    for key in ancestor_keys.intersection(incoming_keys):
        a = ancestor[key]
        i = incoming[key]
        if type(a) is not type(i):
            raise UnmatchableModel(a, i)
        yield from updated_properties(a, i, create)

    if (
        ancestor_style_sheet
        and incoming_style_sheet
        and ancestor_style_sheet.id != incoming_style_sheet.id
    ):
        yield from updated_properties(
            ancestor_style_sheet, incoming_style_sheet, create
        )


def updated_properties(ancestor, incoming, create) -> Iterable[ValueChange | RefChange]:
    ancestor_vals: dict[str, Base | collection[Base] | str | int | None] = {}
    if ancestor:
        ancestor.save(lambda n, v: setitem(ancestor_vals, n, v))
    incoming_vals: dict[str, Base | collection[Base] | str | int | None] = {}
    incoming.save(lambda n, v: setitem(incoming_vals, n, v))

    for name in {*ancestor_vals.keys(), *incoming_vals.keys()}:
        if name == "id":
            continue
        value = incoming_vals.get(name)
        other = ancestor_vals.get(name)
        id = ancestor.id if ancestor else incoming.id
        if isinstance(value, Base):
            # Allow values to be None
            assert other is None or isinstance(other, Base)
            if other is None or value.id != other.id:
                yield create(
                    RefChange,
                    op="update",
                    element_id=id,
                    property_name=name,
                    property_ref=value.id,
                )
        elif isinstance(value, collection):
            assert other is None or isinstance(other, collection)
            other_ids = {o.id for o in other} if other is not None else set()

            yield from (
                create(
                    RefChange,
                    op="add",
                    element_id=id,
                    property_name=name,
                    property_ref=v.id,
                )
                for v in value
                if v.id not in other_ids
            )
        elif value != other:
            if isinstance(other, Base):
                yield create(
                    RefChange,
                    op="update",
                    element_id=id,
                    property_name=name,
                    property_ref=None,
                )
            elif not isinstance(other, collection):
                value_change = create(
                    ValueChange,
                    op="update",
                    element_id=id,
                    property_name=name,
                )
                set_value_change_property_value(value_change, value)
                yield value_change

        if isinstance(other, collection):
            assert value is None or isinstance(value, collection)
            value_ids = {v.id for v in value} if value else set()

            yield from (
                create(
                    RefChange,
                    op="remove",
                    element_id=id,
                    property_name=name,
                    property_ref=o.id,
                )
                for o in other
                if o.id not in value_ids
            )


def set_value_change_property_value(
    value_change: ValueChange, new_value: None | str | int | UnlimitedNatural | bool
):
    if new_value is None:
        value_change.property_value = None
        value_change.property_type = None
    elif isinstance(new_value, str):
        value_change.property_value = new_value
        value_change.property_type = "str"
    elif isinstance(new_value, bool):
        value_change.property_value = str(new_value)
        value_change.property_type = "bool"
    elif isinstance(new_value, int):
        value_change.property_value = str(new_value)
        value_change.property_type = "int"
    elif new_value == "*":
        value_change.property_value = str(new_value)
        value_change.property_type = "UnlimitedNatural"
