"""C4 Model Language entrypoint."""

from gaphor.abc import ModelingLanguage
from gaphor.core.modeling import coremodel


class CoreModelingLanguage(ModelingLanguage):
    @property
    def name(self) -> str:
        return ""

    @property
    def toolbox_definition(self):
        raise ValueError("No toolbox for the core model")

    @property
    def diagram_types(self):
        raise ValueError("No diagram types for the core model")

    @property
    def element_types(self):
        raise ValueError("No element types for the core model")

    @property
    def model_browser_model(self):
        raise ValueError("No model browser model for the core model")

    def lookup_element(self, name, ns=None):
        assert ns in ("Core", None)
        return getattr(coremodel, name, None)


class MockModelingLanguage(ModelingLanguage):
    """This class can be used to instantly combine modeling languages."""

    def __init__(self, *modeling_languages: ModelingLanguage):
        self._modeling_languages = modeling_languages

    @property
    def name(self) -> str:
        return "Mock"

    @property
    def toolbox_definition(self):
        raise ValueError("No toolbox for the mock model")

    @property
    def diagram_types(self):
        raise ValueError("No diagram types for the mock model")

    @property
    def element_types(self):
        raise ValueError("No element types for the mock model")

    @property
    def model_browser_model(self):
        raise ValueError("No model browser model for the mock model")

    def lookup_element(self, name, ns=None):
        if ns:
            # This is sort of hackish.
            # It's better to lookup modeling languages from entry points
            for m in self._modeling_languages:
                if m.__class__.__name__.lower().startswith(ns.lower()):
                    return m.lookup_element(name, ns)

            raise ValueError(
                f"Invalid namespace '{ns}', should be one of {self._modeling_languages}"
            )

        return next(
            filter(
                None,
                [
                    provider.lookup_element(name)
                    for provider in self._modeling_languages
                ],
            ),
            None,
        )
