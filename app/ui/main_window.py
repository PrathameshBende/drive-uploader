"""Main application window."""
"""Main application window."""

import os
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GLib
from app.config import ConfigManager
from app.backend.uploader import UploadManager
from app.logger import setup_logger
logger = setup_logger()

class MainWindow(Adw.ApplicationWindow):
    """The primary window for the backup manager."""

    def __init__(self, application: Adw.Application, config: ConfigManager, **kwargs) -> None:
        super().__init__(application=application, **kwargs)
        self.config = config
        self.upload_manager = UploadManager()
        
        self.set_title("Google Drive Backup Manager")
        self.set_default_size(800, 600)

        self._build_ui()
        self._load_folders()

    def _build_ui(self) -> None:
        """Constructs the UI layout using Libadwaita widgets."""
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header Bar
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Backup Manager", subtitle="Google Drive"))

        self.btn_settings = Gtk.Button(icon_name="open-menu-symbolic", tooltip_text="Settings")
        self.btn_settings.connect("clicked", lambda w: self._show_settings_dialog())
        header.pack_end(self.btn_settings)
        
        # Header buttons
        self.btn_add = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Add Folder")
        self.btn_add.connect("clicked", self._on_add_folder)
        header.pack_start(self.btn_add)

        self.btn_remove = Gtk.Button(icon_name="list-remove-symbolic", tooltip_text="Remove Folder")
        self.btn_remove.connect("clicked", self._on_remove_folder)
        header.pack_start(self.btn_remove)

        # Settings button (Gear icon)
        self.btn_settings = Gtk.Button(icon_name="emblem-system-symbolic", tooltip_text="Settings")
        self.btn_settings.connect("clicked", lambda w: self._show_settings_dialog())
        header.pack_end(self.btn_settings)

        # Upload and Cancel buttons
        self.btn_upload = Gtk.Button(label="Upload", tooltip_text="Start Backup")
        self.btn_upload.add_css_class("suggested-action")
        self.btn_upload.connect("clicked", self._on_upload)
        header.pack_end(self.btn_upload)

        self.btn_cancel = Gtk.Button(label="Cancel", tooltip_text="Cancel Upload")
        self.btn_cancel.add_css_class("destructive-action")
        self.btn_cancel.connect("clicked", self._on_cancel)
        self.btn_cancel.set_sensitive(False)
        header.pack_end(self.btn_cancel)

        main_box.append(header)

        # Content Area
        self.clamp = Adw.Clamp()
        main_box.append(self.clamp)

        content_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, 
            spacing=12, 
            margin_top=12, margin_bottom=12, 
            margin_start=12, margin_end=12
        )
        self.clamp.set_child(content_box)

        # Folder List
        self.folder_list = Gtk.ListBox()
        self.folder_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.folder_list.add_css_class("boxed-list")
        
        frame = Gtk.Frame()
        frame.set_child(self.folder_list)
        content_box.append(frame)

        # Progress & Status
        self.status_label = Gtk.Label(label="Ready", xalign=0)
        self.status_label.add_css_class("dim-label")
        content_box.append(self.status_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        content_box.append(self.progress_bar)

        # Log Window
        log_frame = Gtk.Frame(label="Logs")
        self.log_view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(150)
        scrolled.set_child(self.log_view)
        log_frame.set_child(scrolled)
        
        content_box.append(log_frame)

    def _is_path_valid(self, path: str) -> bool:
        """Checks if a path exists, is a directory, and is readable."""
        p = Path(path)
        try:
            return p.exists() and p.is_dir() and os.access(path, os.R_OK)
        except Exception:
            return False
        
    def _load_folders(self) -> None:
        """Populates the list box with folders from config."""
        logger.info(f"Loading {len(self.config.folders)} folders from config...")
        for folder in self.config.folders:
            name = folder.get("name", "Unknown")
            path = folder.get("path", "")
            logger.info(f"Restoring folder: {name} -> {path}")
            self._add_folder_row(name, path)

    def _add_folder_row(self, name: str, path: str) -> None:
        """Creates and adds a row to the folder list."""
        row = Adw.ActionRow(title=name, subtitle=path)
        row.set_activatable(False)
        
        # Visual warning for invalid/missing paths (e.g., unmounted drive)
        if not self._is_path_valid(path):
            warn_icon = Gtk.Image(icon_name="dialog-warning-symbolic")
            warn_icon.add_css_class("warning") 
            warn_icon.set_tooltip_text("Folder is missing or inaccessible")
            row.add_suffix(warn_icon)

        # Action buttons for the row
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, valign=Gtk.Align.CENTER)
        
        btn_up = Gtk.Button(icon_name="go-up-symbolic")
        btn_up.add_css_class("flat")
        btn_up.connect("clicked", self._on_move_up, row)
        box.append(btn_up)

        btn_down = Gtk.Button(icon_name="go-down-symbolic")
        btn_down.add_css_class("flat")
        btn_down.connect("clicked", self._on_move_down, row)
        box.append(btn_down)

        btn_edit = Gtk.Button(icon_name="document-edit-symbolic")
        btn_edit.add_css_class("flat")
        btn_edit.connect("clicked", self._on_edit_folder, row)
        box.append(btn_edit)

        row.add_suffix(box)
        self.folder_list.append(row)
        self._save_folders_to_config()

    def _save_folders_to_config(self) -> None:
        """Saves the current UI list order to the config file."""
        folders = []
        i = 0
        
        # Iterate until get_row_at_index returns None
        while True:
            row = self.folder_list.get_row_at_index(i)
            if row is None:
                break
                
            folders.append({
                "name": row.get_title() or "",
                "path": row.get_subtitle() or ""
            })
            i += 1
        
        logger.info(f"Saving {len(folders)} folders to config...")
        self.config.folders = folders

    def _show_settings_dialog(self) -> None:
        """Shows the settings dialog to configure backup destination."""
        dialog = Adw.PreferencesDialog(title="Settings")
        
        page = Adw.PreferencesPage()
        dialog.add(page)
        
        # Backup Location Group
        group = Adw.PreferencesGroup(
            title="Backup Location", 
            description="Where to store backups on Google Drive"
        )
        page.add(group)
        
        # Remote name
        remote_row = Adw.EntryRow(
            title="Rclone Remote Name",
            text=self.config.settings.get("rclone_remote", "gdrive")
        )
        remote_row.set_show_apply_button(True)
        group.add(remote_row)
        
        # Backup root folder
        root_row = Adw.EntryRow(
            title="Backup Folder on Drive",
            text=self.config.settings.get("backup_root", "Backups"),
            show_apply_button=True
        )
        # REMOVED: root_row.set_description(...) - EntryRow doesn't have this method
        group.add(root_row)
        
        # Apply button handlers
        def on_remote_apply(*args) -> None:
            self.config.settings["rclone_remote"] = remote_row.get_text()
            self.config.save()
            logger.info(f"Rclone remote updated to: {remote_row.get_text()}")
        
        def on_root_apply(*args) -> None:
            self.config.settings["backup_root"] = root_row.get_text()
            self.config.save()
            logger.info(f"Backup root updated to: {root_row.get_text()}")
        
        remote_row.connect("apply", on_remote_apply)
        root_row.connect("apply", on_root_apply)
        
        dialog.present(self)

    def _show_folder_dialog(self, edit_row: Adw.ActionRow | None = None) -> None:
        """Shows the folder picker dialog."""
        dialog = Gtk.FileDialog(title="Select Folder to Backup")
        
        if edit_row:
            current_path = edit_row.get_subtitle()
            if current_path:
                try:
                    initial_folder = Gio.File.new_for_path(current_path)
                    dialog.set_initial_folder(initial_folder)
                except Exception:
                    pass
        
        def on_folder_selected(dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
            try:
                file = dialog.select_folder_finish(result)
                if file:
                    path = file.get_path()
                    name = file.get_basename()
                    
                    # Validate path immediately
                    if not self._is_path_valid(path):
                        self._show_error_dialog("Invalid Path", f"The selected folder is not accessible:\n{path}")
                        return

                    if self._is_folder_duplicate(path):
                        self._show_error_dialog("Duplicate Folder", f"The folder '{path}' is already in the backup list.")
                        return

                    # Check for duplicates
                    if self._is_folder_duplicate(path):
                        self._show_error_dialog("Duplicate Folder", f"The folder '{path}' is already in the backup list.")
                        return
                    
                    if edit_row:
                        edit_row.set_title(name)
                        edit_row.set_subtitle(path)
                        logger.info(f"Folder updated: {name} -> {path}")
                    else:
                        self._add_folder_row(name, path)
                        logger.info(f"Folder added: {name} ({path})")
                    
                    self._append_log(f"Folder {'updated' if edit_row else 'added'}: {path}\n")
                    self._save_folders_to_config()
            except GLib.Error as e:
                if e.domain != "gtk-dialog-error-quark":
                    logger.error(f"Folder selection error: {e}")
        
        dialog.select_folder(self, None, on_folder_selected)

    def _show_edit_dialog(self, row: Adw.ActionRow) -> None:
        """Shows a dialog to edit folder name."""
        dialog = Adw.AlertDialog(
            heading="Edit Folder",
            body="Modify the folder name and path."
        )
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        name_entry = Adw.EntryRow(title="Name")
        name_entry.set_text(row.get_title())
        content.append(name_entry)
        
        path_entry = Adw.EntryRow(title="Path")
        path_entry.set_text(row.get_subtitle())
        content.append(path_entry)
        
        dialog.set_extra_child(content)
        
        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("save", "_Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog: Adw.AlertDialog, response: str) -> None:
            if response == "save":
                new_name = name_entry.get_text().strip()
                new_path = path_entry.get_text().strip()
                
                if not new_name or not new_path:
                    self._show_error_dialog("Invalid Input", "Both name and path are required.")
                    return

                # Validate path immediately
                if not self._is_path_valid(new_path):
                    self._show_error_dialog("Invalid Path", f"The folder is not accessible:\n{new_path}")
                    return

                # Check for duplicates (excluding the current row)
                if self._is_folder_duplicate(new_path, exclude_row=row):
                    self._show_error_dialog("Duplicate Folder", f"The folder '{new_path}' is already in the backup list.")
                    return
                
                row.set_title(new_name)
                row.set_subtitle(new_path)
                self._save_folders_to_config()
                self._append_log(f"Folder edited: {new_name} -> {new_path}\n")
                logger.info(f"Folder edited via dialog: {new_name} ({new_path})")
        
        dialog.connect("response", on_response)
        dialog.present(self)

    def _is_folder_duplicate(self, path: str, exclude_row: Adw.ActionRow | None = None) -> bool:
        """Checks if a folder path already exists in the list."""
        i = 0
        while True:
            row = self.folder_list.get_row_at_index(i)
            if row is None:
                break
            # Check if path matches and it's not the row currently being edited
            if row is not exclude_row and row.get_subtitle() == path:
                return True
            i += 1
        return False

    def _show_error_dialog(self, heading: str, body: str) -> None:
        """Shows a simple error dialog."""
        dialog = Adw.AlertDialog(heading=heading, body=body)
        dialog.add_response("ok", "_OK")
        dialog.present(self)

    def _append_log(self, message: str) -> None:
        """Appends a message to the log view."""
        buffer = self.log_view.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, message)
        
        # Auto-scroll to bottom
        adj = self.log_view.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    # --- Event Handlers ---
    def _on_add_folder(self, button: Gtk.Button) -> None:
        self._show_folder_dialog()

    def _on_remove_folder(self, button: Gtk.Button) -> None:
        row = self.folder_list.get_selected_row()
        if not row:
            self._append_log("No folder selected for removal.\n")
            return
        
        name = row.get_title()
        path = row.get_subtitle()
        
        dialog = Adw.AlertDialog(
            heading="Remove Folder",
            body=f"Are you sure you want to remove \"{name}\" from the backup list?"
        )
        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("remove", "_Remove")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog: Adw.AlertDialog, response: str) -> None:
            if response == "remove":
                self.folder_list.remove(row)
                self._save_folders_to_config()
                self._append_log(f"Folder removed: {name} ({path})\n")
                logger.info(f"Folder removed: {name}")
        
        dialog.connect("response", on_response)
        dialog.present(self)

    def _on_edit_folder(self, button: Gtk.Button, row: Adw.ActionRow) -> None:
        self._show_edit_dialog(row)

    def _on_move_up(self, button: Gtk.Button, row: Adw.ActionRow) -> None:
        index = row.get_index()
        if index > 0:
            self.folder_list.remove(row)
            self.folder_list.insert(row, index - 1)
            self._save_folders_to_config()
            self._append_log(f"Moved folder up: {row.get_title()}\n")

    def _on_move_down(self, button: Gtk.Button, row: Adw.ActionRow) -> None:
        """Moves the selected row down in the list."""
        index = row.get_index()
        
        # Check if there is a row below the current one
        if self.folder_list.get_row_at_index(index + 1) is not None:
            self.folder_list.remove(row)
            self.folder_list.insert(row, index + 1)
            self._save_folders_to_config()
            self._append_log(f"Moved folder down: {row.get_title()}\n")

    def _on_upload(self, button: Gtk.Button) -> None:
        folders = self.config.folders
        if not folders:
            self._append_log("No folders configured for backup.\n")
            return

        # Filter out invalid folders
        valid_folders = []
        invalid_paths = []
        
        for folder in folders:
            if self._is_path_valid(folder["path"]):
                valid_folders.append(folder)
            else:
                invalid_paths.append(folder["path"])
                self._append_log(f"WARNING: Skipping inaccessible folder: {folder['path']}\n")

        if invalid_paths:
            self._append_log(f"Skipped {len(invalid_paths)} inaccessible folder(s). Check for warning icons.\n")

        if not valid_folders:
            self._show_error_dialog("Upload Failed", "No valid folders found to upload. Please check your paths.")
            return

        # Proceed with valid folders only
        self._set_ui_sensitive(False)
        self.btn_cancel.set_sensitive(True)
        self.btn_upload.set_sensitive(False)
        
        self._append_log(f"Starting backup of {len(valid_folders)} folder(s)...\n")
        logger.info(f"Starting backup of {len(valid_folders)} folder(s)")
        
        self._upload_next_folder(0, valid_folders)

    def _upload_next_folder(self, index: int, folders: list) -> None:
        if index >= len(folders):
            self._on_all_uploads_complete()
            return

        folder = folders[index]
        self._append_log(f"\n--- Uploading folder {index + 1}/{len(folders)} ---\n")
        
        self.upload_manager.upload_folder(
            source_path=folder["path"],
            folder_name=folder["name"],
            remote=self.config.settings["rclone_remote"],
            backup_root=self.config.settings["backup_root"],
            on_progress=self._on_upload_progress,
            on_log=self._append_log,
            on_complete=lambda success, msg: self._on_folder_complete(success, msg, index, folders)
        )

    def _on_upload_progress(self, current_folder: str, current_file: str, percent: float) -> None:
        if percent >= 0:
            self.progress_bar.set_fraction(percent / 100.0)
            self.progress_bar.set_text(f"{percent:.1f}%")
        
        if current_file:
            self.status_label.set_text(f"Uploading: {current_file}")
        else:
            self.status_label.set_text(f"Processing: {current_folder}")

    def _on_folder_complete(self, success: bool, message: str, index: int, folders: list) -> None:
        if not success:
            self._append_log(f"ERROR: {message}\n")
        
        self._upload_next_folder(index + 1, folders)

    def _on_all_uploads_complete(self) -> None:
        self._append_log("\n=== All uploads completed ===\n")
        self._set_ui_sensitive(True)
        self.btn_cancel.set_sensitive(False)
        self.btn_upload.set_sensitive(True)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("")
        self.status_label.set_text("Ready")
        logger.info("All uploads completed")

    def _on_cancel(self, button: Gtk.Button) -> None:
        self._append_log("Cancelling upload...\n")
        self.upload_manager.cancel()

    def _set_ui_sensitive(self, sensitive: bool) -> None:
        self.btn_add.set_sensitive(sensitive)
        self.btn_remove.set_sensitive(sensitive)
        self.folder_list.set_sensitive(sensitive)