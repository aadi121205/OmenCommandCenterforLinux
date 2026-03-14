#!/usr/bin/env bash
# HP Laptop Manager - Unified Setup Tool
# Handles installation, uninstallation, and updates.

set -euo pipefail

# --- CONFIGURATION ---
APP_NAME="HP Laptop Manager"
INSTALL_DIR="/usr/libexec/hp-manager"
DATA_DIR="/usr/share/hp-manager"
BIN_LINK="/usr/bin/hp-manager"
UNINSTALLER_LINK="/usr/bin/hp-manager-uninstall"
CONFIG_DIR="/etc/hp-manager"
VERSION="1.1.2"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging helpers
log()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
err()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }
info()  { echo -e "${CYAN}[i]${NC} $*"; }
debug() { echo -e "${BLUE}[DEBUG]${NC} $*"; }

# Language detection
LANG_CODE=${LANG:0:2}

# --- I18N MESSAGES ---
msg() {
    local key=$1
    shift
    if [ "$LANG_CODE" == "tr" ]; then
        case $key in
            "root_check") echo "Bu scripti root olarak çalıştırın: sudo $0" ;;
            "pm_not_found") echo "Desteklenen paket yöneticisi bulunamadı (pacman/apt/dnf/zypper)" ;;
            "pm_name") echo "Paket yöneticisi: $1" ;;
            "installing_deps") echo "Bağımlılıklar yükleniyor..." ;;
            "deps_installed") echo "Bağımlılıklar yüklendi" ;;
            "installing_app") echo "Uygulama kuruluyor..." ;;
            "daemon_installed") echo "Daemon kuruldu: $1" ;;
            "gui_installed") echo "GUI kuruldu: $1" ;;
            "images_copied") echo "Resimler kopyalandı" ;;
            "success") echo "${APP_NAME} başarıyla kuruldu!" ;;
            "uninstalling") echo "Uygulama kaldırılıyor..." ;;
            "uninstalled") echo "Uygulama kaldırıldı" ;;
            "updating") echo "Uygulama güncelleniyor..." ;;
            "updated") echo "Güncelleme tamamlandı!" ;;
            "usage") echo "Kullanım: $0 [install|uninstall|update]" ;;
            "select_power_manager") echo -e "\nHangi güç yöneticisini kullanmak istersiniz?" ;;
            "pm_detected") echo -e "${CYAN}[i]${NC} Sistemde tespit edildi: $1" ;;
            "pm_opt_1") echo "1) power-profiles-daemon (Varsayılan)" ;;
            "pm_opt_2") echo "2) ppd-tuned (Fedora kullanıyorsanız önerilir)" ;;
            "pm_opt_3") echo "3) TLP (https://github.com/linrunner/TLP)" ;;
            "pm_opt_4") echo "4) auto-cpufreq (https://github.com/AdnanHodzic/auto-cpufreq)" ;;
            "pm_opt_5") echo "5) Atla (Herhangi bir güç yöneticisi kurma)" ;;
            "pm_choice") echo "Seçiminiz (1-5): " ;;
            "installing_pm") echo "$1 kuruluyor..." ;;
            "pm_not_in_repo") echo "Uyarı: $1 paket yöneticinizde bulunamadı. Lütfen manuel kurun." ;;
            "skipping_pm") echo "Güç yöneticisi kurulumu atlanıyor." ;;
            *) echo "$key" ;;
        esac
    else
        case $key in
            "root_check") echo "Run this script as root: sudo $0" ;;
            "pm_not_found") echo "Supported package manager not found (pacman/apt/dnf/zypper)" ;;
            "pm_name") echo "Package manager: $1" ;;
            "installing_deps") echo "Installing dependencies..." ;;
            "deps_installed") echo "Dependencies installed" ;;
            "installing_app") echo "Installing application..." ;;
            "daemon_installed") echo "Daemon installed: $1" ;;
            "gui_installed") echo "GUI installed: $1" ;;
            "images_copied") echo "Images copied" ;;
            "success") echo "${APP_NAME} successfully installed!" ;;
            "uninstalling") echo "Uninstalling application..." ;;
            "uninstalled") echo "Application uninstalled" ;;
            "updating") echo "Updating application..." ;;
            "updated") echo "Update complete!" ;;
            "usage") echo "Usage: $0 [install|uninstall|update]" ;;
            "select_power_manager") echo -e "\nWhich power manager would you like to use?" ;;
            "pm_detected") echo -e "${CYAN}[i]${NC} Detected on system: $1" ;;
            "pm_opt_1") echo "1) power-profiles-daemon (Default)" ;;
            "pm_opt_2") echo "2) ppd-tuned (Recommended for Fedora users)" ;;
            "pm_opt_3") echo "3) TLP (https://github.com/linrunner/TLP)" ;;
            "pm_opt_4") echo "4) auto-cpufreq (https://github.com/AdnanHodzic/auto-cpufreq)" ;;
            "pm_opt_5") echo "5) Skip (Don't install any power manager)" ;;
            "pm_choice") echo "Your choice (1-5): " ;;
            "installing_pm") echo "Installing $1..." ;;
            "pm_not_in_repo") echo "Warning: $1 was not found in your package manager. Please install it manually." ;;
            "skipping_pm") echo "Skipping power manager installation." ;;
            *) echo "$key" ;;
        esac
    fi
}

# --- ROOT CHECK ---
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        err "$(msg root_check)"
    fi
}

# --- DISTRO DETECTION ---
detect_pm() {
    if [ -f /etc/os-release ]; then
        _DISTRO_NAME=$(. /etc/os-release && echo "${PRETTY_NAME:-$NAME}")
        info "Detected distro: $_DISTRO_NAME"
    fi

    if [ -f /etc/fedora-release ] || [ -f /etc/nobara-release ] || command -v dnf &>/dev/null; then
        PM="dnf"
        INSTALL_CMD="dnf install -y"
    elif command -v pacman &>/dev/null; then
        PM="pacman"
        INSTALL_CMD="pacman -S --noconfirm --needed"
    elif command -v apt &>/dev/null; then
        PM="apt"
        INSTALL_CMD="apt install -y"
    elif command -v zypper &>/dev/null; then
        PM="zypper"
        INSTALL_CMD="zypper install -y"
    else
        err "$(msg pm_not_found)"
    fi
    log "$(msg pm_name $PM)"
}

# --- INSTALL DEPENDENCIES ---
install_dependencies() {
    info "$(msg installing_deps)"
    
    # Core packages
    case $PM in
        pacman)
            $INSTALL_CMD python python-gobject gtk4 libadwaita python-pydbus python-cairo evtest
            ;;
        apt)
            $INSTALL_CMD python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-pydbus python3-cairo evtest
            ;;
        dnf|zypper)
            $INSTALL_CMD python3 python3-gobject gtk4 libadwaita python3-pydbus python3-cairo evtest
            ;;
    esac

    # Power Manager Detection
    local detected=()
    if systemctl list-unit-files power-profiles-daemon.service 2>/dev/null | grep -q "power-profiles-daemon"; then
        detected+=("power-profiles-daemon")
    fi
    command -v tlp &>/dev/null && detected+=("TLP")
    command -v auto-cpufreq &>/dev/null && detected+=("auto-cpufreq")
    if command -v tuned &>/dev/null || { command -v rpm &>/dev/null && rpm -q tuned &>/dev/null 2>/dev/null; }; then
        detected+=("tuned")
    fi

    # Power Manager Selection
    msg select_power_manager
    if [ ${#detected[@]} -gt 0 ]; then
        msg pm_detected "${detected[*]}"
    fi

    msg pm_opt_1
    msg pm_opt_2
    msg pm_opt_3
    msg pm_opt_4
    msg pm_opt_5
    echo -n "$(msg pm_choice)"
    read -r choice

    case $choice in
        2)
            local pkg="tuned-ppd"
            info "$(msg installing_pm $pkg)"
            $INSTALL_CMD $pkg || warn "$(msg pm_not_in_repo $pkg)"
            ;;
        3)
            local pkg="tlp"
            info "$(msg installing_pm $pkg)"
            $INSTALL_CMD $pkg || warn "$(msg pm_not_in_repo $pkg)"
            ;;
        4)
            local pkg="auto-cpufreq"
            info "$(msg installing_pm $pkg)"
            $INSTALL_CMD $pkg || warn "$(msg pm_not_in_repo $pkg)"
            ;;
        5)
            info "$(msg skipping_pm)"
            ;;
        *)
            local pkg="power-profiles-daemon"
            info "$(msg installing_pm $pkg)"
            $INSTALL_CMD $pkg || warn "$(msg pm_not_in_repo $pkg)"
            ;;
    esac

    log "$(msg deps_installed)"
}

# --- DRIVER MANAGEMENT ---
manage_driver() {
    local action=$1
    if [ -d "driver" ] && [ -f "driver/install.sh" ]; then
        info "Running driver ${action}..."
        (cd driver && chmod +x install.sh && ./install.sh "$action") || warn "Driver ${action} failed."
    else
        warn "Driver directory or install script not found!"
    fi
}

# --- INSTALL APP ---
do_install() {
    check_root
    detect_pm
    install_dependencies
    
    info "$(msg installing_app)"
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR/images"
    mkdir -p "$CONFIG_DIR"

    # Driver
    manage_driver "install"

    # App Files
    cp -r src/daemon/* "$INSTALL_DIR/"
    
    mkdir -p "$DATA_DIR/gui/pages"
    mkdir -p "$DATA_DIR/gui/widgets"
    cp src/gui/main_window.py "$DATA_DIR/gui/"
    cp src/gui/i18n.py "$DATA_DIR/gui/"
    cp src/gui/pages/*.py "$DATA_DIR/gui/pages/"
    cp src/gui/widgets/*.py "$DATA_DIR/gui/widgets/"
    
    if [ -d "images" ]; then
        cp images/* "$DATA_DIR/images/" 2>/dev/null || true
    fi

    # Launcher
    cat > "$BIN_LINK" << LAUNCHER
#!/bin/bash
cd /usr/share/hp-manager/gui
exec python3 /usr/share/hp-manager/gui/main_window.py "\$@"
LAUNCHER
    chmod +x "$BIN_LINK"

    # System Integration
    mkdir -p /etc/dbus-1/system.d
    mkdir -p /usr/share/polkit-1/actions
    mkdir -p /usr/share/applications
    
    cp data/com.yyl.hpmanager.conf /etc/dbus-1/system.d/
    cp data/com.yyl.hpmanager.service /etc/systemd/system/com.yyl.hpmanager.service
    cp data/com.yyl.hpmanager.policy /usr/share/polkit-1/actions/
    cp data/com.yyl.hpmanager.desktop /usr/share/applications/
    
    # Omen Key
    if [ -f data/90-hp-omen-key.rules ]; then
        cp data/90-hp-omen-key.rules /etc/udev/rules.d/
    fi
    if [ -f data/hp-omen-key.service ]; then
        cp data/hp-omen-key.service /etc/systemd/system/
    fi
    if [ -f data/omen-key-listener.sh ]; then
        cp data/omen-key-listener.sh /usr/libexec/hp-manager/
        chmod +x /usr/libexec/hp-manager/omen-key-listener.sh
    fi

    # Boot load for RGB
    MODULES_LOAD_FILE="/etc/modules-load.d/hp-rgb-lighting.conf"
    echo "hp-rgb-lighting" > "$MODULES_LOAD_FILE"

    systemctl daemon-reload
    systemctl enable com.yyl.hpmanager.service
    systemctl enable hp-omen-key.service 2>/dev/null || true
    systemctl restart com.yyl.hpmanager.service || warn "Daemon failed to start."
    systemctl restart hp-omen-key.service 2>/dev/null || true

    # Unified Uninstaller Link
    cat > "$UNINSTALLER_LINK" << UNINSTALLER
#!/bin/bash
sudo $0 uninstall
UNINSTALLER
    chmod +x "$UNINSTALLER_LINK"

    log "$(msg success)"
}

# --- UNINSTALL APP ---
do_uninstall() {
    check_root
    info "$(msg uninstalling)"
    
    systemctl stop hp-manager.service com.yyl.hpmanager.service 2>/dev/null || true
    systemctl disable hp-manager.service com.yyl.hpmanager.service 2>/dev/null || true
    systemctl stop hp-omen-key.service 2>/dev/null || true
    systemctl disable hp-omen-key.service 2>/dev/null || true
    
    manage_driver "uninstall"

    rm -f /etc/systemd/system/hp-manager.service
    rm -f /etc/systemd/system/com.yyl.hpmanager.service
    rm -f /etc/systemd/system/hp-omen-key.service
    rm -f "$BIN_LINK"
    rm -f "$UNINSTALLER_LINK"
    rm -rf "$INSTALL_DIR"
    rm -rf "$DATA_DIR"
    rm -f /etc/dbus-1/system.d/com.yyl.hpmanager.conf
    rm -f /usr/share/polkit-1/actions/com.yyl.hpmanager.policy
    rm -f /usr/share/applications/com.yyl.hpmanager.desktop
    rm -f /usr/share/icons/hicolor/48x48/apps/hp_logo.png
    rm -f /etc/udev/rules.d/90-hp-omen-key.rules
    rm -f /etc/modules-load.d/hp-rgb-lighting.conf
    
    systemctl daemon-reload
    log "$(msg uninstalled)"
}

# --- UPDATE APP ---
do_update() {
    info "$(msg updating)"
    
    if [ -d ".git" ]; then
        info "Pulling latest changes..."
        git stash || true
        git pull
    fi
    
    do_uninstall
    do_install
    
    log "$(msg updated)"
}

# --- MAIN ---
case "${1:-install}" in
    install)   do_install ;;
    uninstall) do_uninstall ;;
    update)    do_update ;;
    *) echo "$(msg usage)"; exit 1 ;;
esac
