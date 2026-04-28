#!/usr/bin/env bash
# HP RGB Control — Quick reinstall (stops service, copies files, restarts).
# Skips the driver rebuild — use setup.sh install for a full fresh install.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo $0"
    exit 1
fi

INSTALL_DIR="/usr/libexec/hp-manager"
DATA_DIR="/usr/share/hp-manager"

echo "[i] Stopping daemon..."
systemctl stop com.aadi.hpmanager.service 2>/dev/null || true

echo "[i] Copying daemon files..."
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/src/daemon/"* "$INSTALL_DIR/"

echo "[i] Copying GUI files..."
mkdir -p "$DATA_DIR/gui/pages"
mkdir -p "$DATA_DIR/gui/widgets"
cp "$SCRIPT_DIR/src/gui/main_window.py" "$DATA_DIR/gui/"
cp "$SCRIPT_DIR/src/gui/i18n.py"        "$DATA_DIR/gui/"
cp "$SCRIPT_DIR/src/gui/pages/"*.py     "$DATA_DIR/gui/pages/"
cp "$SCRIPT_DIR/src/gui/widgets/"*.py   "$DATA_DIR/gui/widgets/"

echo "[i] Restarting daemon..."
systemctl start com.aadi.hpmanager.service

echo "[✓] Reinstall complete."
echo "    Daemon status: $(systemctl is-active com.aadi.hpmanager.service 2>/dev/null || echo unknown)"
