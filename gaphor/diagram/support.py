"""For ease of creation, maintain a mapping from Base to Diagram Item."""

from gaphor.core.modeling import Base, Presentation


def represents(uml_element, **metadata):
    """A decorator to assign a default Base type to a diagram item."""

    def wrapper(presentation):
        set_diagram_item(uml_element, presentation, metadata)
        return presentation

    return wrapper


# Map elements to their (default) representation.
_element_to_item_map: dict[type[Base], type[Presentation]] = {}
_item_to_metadata_map: dict[type[Presentation], dict[str, object]] = {}


def get_diagram_item(element_cls: type[Base]) -> type[Presentation] | None:
    global _element_to_item_map
    return _element_to_item_map.get(element_cls)


def get_diagram_item_metadata(item_cls: type[Presentation]):
    global _item_to_metadata_map
    return _item_to_metadata_map.get(item_cls, {})


def get_model_element(item_cls):
    global _element_to_item_map
    elements = [
        element
        for element, presentation in _element_to_item_map.items()
        if item_cls is presentation
    ]
    return elements[0] if elements else None


def set_diagram_item(element, item, metadata):
    assert element not in _element_to_item_map
    _element_to_item_map[element] = item
    _item_to_metadata_map[item] = metadata
