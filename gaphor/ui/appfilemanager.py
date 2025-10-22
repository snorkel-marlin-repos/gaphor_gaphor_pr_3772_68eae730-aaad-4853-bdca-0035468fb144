import logging
import os.path
from pathlib import Path

from gi.repository import Adw

from gaphor.abc import ActionProvider, Service
from gaphor.asyncio import TaskOwner
from gaphor.core import action, gettext
from gaphor.ui.filedialog import GAPHOR_FILTER, open_file_dialog

log = logging.getLogger(__name__)


class AppFileManager(Service, ActionProvider, TaskOwner):
    """Handle application level file loading."""

    def __init__(self, application):
        super().__init__()
        self.application = application
        self.last_dir = None

    def shutdown(self):
        self.cancel_background_task()

    @property
    def window(self):
        return self.application.active_window

    @action(name="app.file-open")
    def action_open(self):
        """This menu action opens the standard model open dialog."""

        async def open_files():
            filenames: list[Path] | None = await open_file_dialog(  # type: ignore[assignment]
                gettext("Open a Model"),
                parent=self.window,
                dirname=self.last_dir,
                filters=GAPHOR_FILTER,
            )
            if not filenames:
                return

            for filename in filenames:
                if any(
                    session
                    for session in self.application.sessions
                    if session.filename == filename
                ):
                    name = Path(filename).name
                    title = gettext("Switch to {name}?").format(name=name)
                    body = gettext(
                        "{name} is already opened. Do you want to switch to the opened window instead?"
                    ).format(name=name)

                    # Should show only one dialog at a time

                    dialog = Adw.MessageDialog.new(
                        self.window,
                        title,
                    )
                    dialog.set_body(body)
                    dialog.add_response("open", gettext("Open Again"))
                    dialog.add_response("switch", gettext("Switch"))
                    dialog.set_response_appearance(
                        "switch", Adw.ResponseAppearance.SUGGESTED
                    )
                    dialog.set_default_response("switch")
                    dialog.set_close_response("open")
                    dialog.present()
                    answer = await dialog.choose()
                    dialog.destroy()
                    self.application.new_session(
                        filename=filename, force=(answer == "open")
                    )
                else:
                    self.application.new_session(filename=filename)

                self.last_dir = os.path.dirname(filename)

        self.create_background_task(open_files())
