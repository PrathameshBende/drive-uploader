#!/usr/bin/env python3
"""Entry point for the Google Drive Backup Manager."""

import sys
import os
import traceback
import gi

# Add the application directory to Python path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from app.logger import setup_logger
from app.config import ConfigManager
from app.ui.application import BackupApplication

logger = setup_logger()

def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """Global exception handler to prevent silent crashes."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Format the traceback for the user
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Show error dialog in the main thread
    GLib.idle_add(show_error_dialog, error_msg)

def show_error_dialog(error_msg: str) -> None:
    """Displays a fatal error dialog."""
    dialog = Adw.AlertDialog(
        heading="Unexpected Error",
        body="The application encountered a fatal error. Please check the logs."
    )
    dialog.add_response("ok", "_OK")
    dialog.present(None) # Present without a specific parent if app isn't fully loaded

def main() -> int:
    """Initializes the application and starts the GTK main loop."""
    # Set global exception hook
    sys.excepthook = handle_exception
    
    logger.info("Starting Google Drive Backup Manager...")
    
    try:
        config = ConfigManager()
        app = BackupApplication(config=config)
        
        logger.info("Launching UI...")
        return app.run(sys.argv)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())