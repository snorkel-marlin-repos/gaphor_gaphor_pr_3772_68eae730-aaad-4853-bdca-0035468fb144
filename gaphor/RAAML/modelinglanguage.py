"""The RAAML Modeling Language module is the entrypoint for RAAML related
assets."""

from collections.abc import Iterable

from gaphor.abc import ModelingLanguage
from gaphor.core import gettext
from gaphor.diagram.diagramtoolbox import (
    DiagramType,
    ElementCreateInfo,
    ToolboxDefinition,
)
from gaphor.diagram.support import represents
from gaphor.RAAML import diagramitems, raaml
from gaphor.RAAML.toolbox import (
    raaml_diagram_types,
    raaml_element_types,
    raaml_toolbox_actions,
)
from gaphor.UML.general.diagramitem import DiagramItem
from gaphor.UML.treemodel import TreeModel

represents(raaml.FTADiagram)(DiagramItem)
represents(raaml.STPADiagram)(DiagramItem)


class RAAMLModelingLanguage(ModelingLanguage):
    @property
    def name(self) -> str:
        return gettext("RAAML")

    @property
    def toolbox_definition(self) -> ToolboxDefinition:
        return raaml_toolbox_actions

    @property
    def diagram_types(self) -> Iterable[DiagramType]:
        yield from raaml_diagram_types

    @property
    def element_types(self) -> Iterable[ElementCreateInfo]:
        yield from raaml_element_types

    @property
    def model_browser_model(self) -> type[TreeModel]:
        return TreeModel

    def lookup_element(self, name, ns=None):
        assert ns in ("RAAML", None)
        return getattr(raaml, name, None) or getattr(diagramitems, name, None)
