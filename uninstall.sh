#!/bin/bash
set -e

APP_NAME="gdrive-backup-manager"
INSTALL_DIR="/opt/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"
ICON_FILE="/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg"

echo "=== Google Drive Backup Manager Uninstaller ==="

PURGE=false
if [[ "$1" == "--purge" ]]; then
    PURGE=true
fi

# 1. Remove application files
if [ -d "$INSTALL_DIR" ]; then
    echo "Removing application files..."
    sudo rm -rf "$INSTALL_DIR"
else
    echo "Application directory not found."
fi

# 2. Remove desktop entry
if [ -f "$DESKTOP_FILE" ]; then
    echo "Removing desktop launcher..."
    sudo rm -f "$DESKTOP_FILE"
    sudo update-desktop-database
fi

# 3. Remove icon
if [ -f "$ICON_FILE" ]; then
    echo "Removing icon..."
    sudo rm -f "$ICON_FILE"
    gtk-update-icon-cache /usr/share/icons/hicolor/
fi

# 4. Purge config and logs if requested
if [ "$PURGE" = true ]; then
    echo "Purging configuration and logs..."
    rm -rf ~/.config/$APP_NAME
    rm -rf ~/.local/share/$APP_NAME
else
    echo "Keeping configuration and logs in ~/.config/$APP_NAME and ~/.local/share/$APP_NAME"
    echo "To remove them, run: ./uninstall.sh --purge"
fi

echo "=== Uninstallation Complete ==="