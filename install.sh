#!/bin/bash
set -e
# At the top of install.sh
INSTALL_PREFIX="${INSTALL_PREFIX:-/opt}"
APP_NAME="gdrive-backup-manager"
INSTALL_DIR="$INSTALL_PREFIX/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"
ICON_DIR="/usr/share/icons/hicolor/scalable/apps"
ICON_FILE="$ICON_DIR/gdrive-backup-manager.png"

echo "=== Google Drive Backup Manager Installer ==="

# 1. Check dependencies
echo "Checking dependencies..."
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is not installed."; exit 1; }
command -v rclone >/dev/null 2>&1 || { echo "Error: rclone is not installed. Run: sudo dnf install rclone"; exit 1; }

python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1'); from gi.repository import Gtk, Adw" >/dev/null 2>&1 || {
    echo "Error: GTK4 or Libadwaita not found. Run: sudo dnf install python3-gobject gtk4 libadwaita"
    exit 1
}

# 2. Create directories
echo "Creating directories..."
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p ~/.config/$APP_NAME
sudo mkdir -p ~/.local/share/$APP_NAME/logs

# 3. Copy files
echo "Installing application files..."
sudo cp -r ./* "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/run.py"

# 4. Install Desktop Entry
echo "Installing desktop launcher..."
sudo cp resources/$APP_NAME.desktop "$DESKTOP_FILE"
sudo sed -i "s|Exec=python3 /opt/$APP_NAME/run.py|Exec=python3 $INSTALL_DIR/run.py|g" "$DESKTOP_FILE"

# 5. Install Icon
echo "Installing icon..."
sudo mkdir -p "$ICON_DIR"
sudo cp resources/gdrive-backup-manager.png "$ICON_FILE"

# 6. Update desktop database
sudo update-desktop-database
gtk-update-icon-cache "$ICON_DIR/.."

echo "=== Installation Successful! ==="
echo "You can now launch '$APP_NAME' from your application menu."