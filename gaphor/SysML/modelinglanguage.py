"""The SysML Modeling Language module is the entrypoint for SysML related
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
from gaphor.SysML import diagramitems, sysml
from gaphor.SysML.toolbox import (
    sysml_diagram_types,
    sysml_element_types,
    sysml_toolbox_actions,
)
from gaphor.UML.general.diagramitem import DiagramItem
from gaphor.UML.treemodel import TreeModel

for _type in (
    sysml.ActivityDiagram,
    sysml.BlockDefinitionDiagram,
    sysml.InternalBlockDiagram,
    sysml.PackageDiagram,
    sysml.RequirementDiagram,
    sysml.SequenceDiagram,
    sysml.StateMachineDiagram,
    sysml.UseCaseDiagram,
):
    represents(_type)(DiagramItem)


class SysMLModelingLanguage(ModelingLanguage):
    @property
    def name(self) -> str:
        return gettext("SysML")

    @property
    def toolbox_definition(self) -> ToolboxDefinition:
        return sysml_toolbox_actions

    @property
    def diagram_types(self) -> Iterable[DiagramType]:
        yield from sysml_diagram_types

    @property
    def element_types(self) -> Iterable[ElementCreateInfo]:
        yield from sysml_element_types

    @property
    def model_browser_model(self) -> type[TreeModel]:
        return TreeModel

    def lookup_element(self, name, ns=None):
        assert ns in ("SysML", None)
        return getattr(sysml, name, None) or getattr(diagramitems, name, None)
