"""Application settings support for Gaphor."""

import hashlib
import logging
import sys
from enum import Enum
from pathlib import Path

from gi.repository import Gio, GLib

APPLICATION_ID = "org.gaphor.Gaphor"

logger = logging.getLogger(__name__)


def get_config_dir() -> Path:
    """Return the directory where the user's config is stored.

    This varies depending on platform.
    """

    config_dir = Path(GLib.get_user_config_dir()) / "gaphor"
    config_dir.mkdir(exist_ok=True, parents=True)

    return config_dir


def get_cache_dir() -> Path:
    """Return the directory where the user's cache is stored.

    This varies depending on platform.
    """

    cache_dir = Path(GLib.get_user_cache_dir()) / "gaphor"
    cache_dir.mkdir(exist_ok=True, parents=True)

    return cache_dir


def file_hash(filename) -> str:
    return hashlib.blake2b(str(filename).encode("utf-8"), digest_size=24).hexdigest()


class StyleVariant(Enum):
    SYSTEM = 0
    DARK = 1
    LIGHT = 2


class Settings:
    """Gaphor settings."""

    _required_keys = [
        "use-english",
        "style-variant",
        "reset-tool-after-create",
        "remove-unused-elements",
    ]

    def __init__(self):
        self._gio_settings = (
            Gio.Settings.new(APPLICATION_ID)
            if (schema_source := Gio.SettingsSchemaSource.get_default())
            and (schema := schema_source.lookup(APPLICATION_ID, False))
            and (schema_keys := schema.list_keys())
            and all(key in schema_keys for key in self._required_keys)
            else None
        )

        if not self._gio_settings:
            # Workaround: do not show this message if we're installing schemas
            if "install-schemas" not in sys.argv:
                logger.warning(
                    "Settings schema not found and settings won’t be saved. Run `gaphor install-schemas`."
                )

    @property
    def style_variant(self) -> StyleVariant:
        return (
            StyleVariant(self._gio_settings.get_enum("style-variant"))
            if self._gio_settings
            else StyleVariant.SYSTEM
        )

    @style_variant.setter
    def style_variant(self, style_variant: StyleVariant):
        if self._gio_settings:
            self._gio_settings.set_enum("style-variant", style_variant.value)

    def bind_style_variant(self, target, prop):
        # Bind with mapping not supported by PyGObject: https://gitlab.gnome.org/GNOME/pygobject/-/issues/98
        # To bind to a function that can map between guint and a string
        if self._gio_settings:
            style_variant = self._gio_settings.get_enum("style-variant")
            target.set_property(prop, style_variant)

    def style_variant_changed(self, callback):
        if self._gio_settings:

            def _on_changed(_settings, _name):
                callback(self.style_variant)

            self._gio_settings.connect("changed::style-variant", _on_changed)
            callback(self.style_variant)

    @property
    def use_english(self) -> bool:
        return (
            self._gio_settings.get_boolean("use-english")
            if self._gio_settings
            else False
        )

    def bind_use_english(self, target, prop):
        self._bind_propery("use-english", target, prop)

    @property
    def reset_tool_after_create(self):
        return (
            self._gio_settings.get_boolean("reset-tool-after-create")
            if self._gio_settings
            else True
        )

    def bind_reset_tool_after_create(self, target, prop):
        self._bind_propery("reset-tool-after-create", target, prop)

    @property
    def remove_unused_elements(self):
        return (
            self._gio_settings.get_boolean("remove-unused-elements")
            if self._gio_settings
            else True
        )

    def bind_remove_unused_elements(self, target, prop):
        self._bind_propery("remove-unused-elements", target, prop)

    def _bind_propery(self, name, target, prop):
        if self._gio_settings:
            self._gio_settings.bind(name, target, prop, Gio.SettingsBindFlags.DEFAULT)


settings = Settings()
