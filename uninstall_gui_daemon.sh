#!/usr/bin/env bash
# OMEN Command Center for Linux — Targeted Uninstaller
# Removes the Daemon and GUI components only. Leaves DKMS drivers untouched.

set -euo pipefail

# --- CONFIGURATION ---
INSTALL_DIR="/usr/libexec/hp-manager"
DATA_DIR="/usr/share/hp-manager"
BIN_LINK="/usr/bin/hp-manager"
UNINSTALLER_LINK="/usr/bin/hp-manager-uninstall"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $*"; }
err() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# --- ROOT CHECK ---
if [ "$(id -u)" -ne 0 ]; then
    err "Run this script as root: sudo $0"
fi

echo "Uninstalling OMEN Command Center (Daemon & GUI only)..."

# 1. Stop and Disable Services
echo "Stopping and disabling services..."
systemctl stop    com.aadi.hpmanager.service 2>/dev/null || true
systemctl disable com.aadi.hpmanager.service 2>/dev/null || true

# 2. Remove Application Files
echo "Removing application files..."
rm -rf "$INSTALL_DIR"
rm -rf "$DATA_DIR"
rm -f  "$BIN_LINK"
rm -f  "$UNINSTALLER_LINK"

# 3. Remove System Integration Files
echo "Removing system integration files..."
rm -f /etc/systemd/system/com.aadi.hpmanager.service
rm -f /etc/dbus-1/system.d/com.aadi.hpmanager.conf
rm -f /usr/share/polkit-1/actions/com.aadi.hpmanager.policy
rm -f /usr/share/applications/com.aadi.hpmanager.desktop
rm -f /usr/share/icons/hicolor/48x48/apps/omenapplogo.png 2>/dev/null || true

# 4. Finalize
systemctl daemon-reload
log "Daemon and GUI have been uninstalled."
echo "NOTE: DKMS drivers and their boot-load configuration were not touched."
