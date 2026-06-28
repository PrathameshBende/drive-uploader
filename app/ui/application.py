"""Main Application class using Libadwaita."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from app.ui.main_window import MainWindow
from app.config import ConfigManager
from app.logger import setup_logger

logger = setup_logger()

class BackupApplication(Adw.Application):
    """The main GTK4/Libadwaita application."""

    def __init__(self, config: ConfigManager) -> None:
        super().__init__(
            application_id="com.github.gdrivebackupmanager",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.config = config
        self.window: MainWindow | None = None

    def do_activate(self) -> None:
        """Called when the application is activated."""
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self, config=self.config)
            self.window = win
        win.present()
        logger.info("Application window activated.")

    def do_shutdown(self) -> None:
        """Called when the application is shutting down."""
        logger.info("Application shutting down...")
        
        # Cancel any ongoing uploads
        if self.window and self.window.upload_manager:
            if self.window.upload_manager.is_running():
                logger.info("Cancelling active upload on shutdown...")
                self.window.upload_manager.cancel()
        
        # Call parent shutdown correctly
        Adw.Application.do_shutdown(self)
