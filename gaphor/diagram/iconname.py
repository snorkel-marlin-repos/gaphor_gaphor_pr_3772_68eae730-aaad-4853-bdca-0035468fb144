"""With `icon_name` you can retrieve an icon name for a model element."""

import re
from functools import singledispatch

from gaphor.core.modeling import Diagram

TO_KEBAB = re.compile(r"([a-z0-9])([A-Z]+)")


def to_kebab_case(s):
    return TO_KEBAB.sub("\\1-\\2", s).lower()


def get_default_icon_name(element):
    """Get an icon name for a model element."""
    return f"gaphor-{to_kebab_case(element.__class__.__name__)}-symbolic"


icon_name = singledispatch(get_default_icon_name)


@icon_name.register(Diagram)
def get_name_for_diagram(_element):
    return "gaphor-diagram-symbolic"
