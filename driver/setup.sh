#!/usr/bin/env bash
# install.sh — Multi-distro installer for hp-wmi-fan-and-backlight-control
# https://github.com/TUXOV/hp-wmi-fan-and-backlight-control
#
# Supports: Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE, Void, Gentoo
# Usage: sudo ./install.sh [install|uninstall]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODNAME="hp-rgb-lighting"
MODVER=$(grep -oP 'PACKAGE_VERSION="\K[^"]+' dkms.conf 2>/dev/null || echo "1.1.1")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Kernel version detection ──────────────────────────────────────────────────
# Kernel 7.0+ has Omen/Victus fan control in the stock hp-wmi module.
# Robust version comparison:
KVER_MAJOR=$(uname -r | cut -d. -f1)
KVER_MINOR=$(uname -r | cut -d. -f2)
STOCK_FAN_SUPPORT=false
if [ "$KVER_MAJOR" -gt 7 ] || { [ "$KVER_MAJOR" -eq 7 ] && [ "$KVER_MINOR" -ge 0 ]; }; then
    STOCK_FAN_SUPPORT=true
fi

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Distro detection ──────────────────────────────────────────────────────────

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_ID="${ID:-unknown}"
        DISTRO_LIKE="${ID_LIKE:-$DISTRO_ID}"
    elif [ -f /etc/arch-release ]; then
        DISTRO_ID="arch"
        DISTRO_LIKE="arch"
    elif [ -f /etc/gentoo-release ]; then
        DISTRO_ID="gentoo"
        DISTRO_LIKE="gentoo"
    else
        DISTRO_ID="unknown"
        DISTRO_LIKE="unknown"
    fi
}

# ── Dependency installation per distro ────────────────────────────────────────

install_deps() {
    info "Detected distro: ${DISTRO_ID}"

    case "$DISTRO_ID" in
        ubuntu|debian|linuxmint|pop|elementary|zorin|kali)
            info "Installing dependencies (apt)..."
            apt-get update -qq
            apt-get install -y dkms build-essential linux-headers-"$(uname -r)"
            ;;
        fedora|nobara)
            info "Installing dependencies (dnf)..."
            dnf install -y dkms kernel-devel kernel-headers gcc make
            ;;
        rhel|centos|rocky|alma)
            info "Installing dependencies (dnf/yum)..."
            if command -v dnf &>/dev/null; then
                dnf install -y dkms kernel-devel kernel-headers gcc make
            else
                yum install -y dkms kernel-devel kernel-headers gcc make
            fi
            ;;
        arch|manjaro|endeavouros|garuda|cachyos)
            info "Installing dependencies (pacman)..."
            # Arch kernel header detection
            local HEADERS_PKG=""
            local RUNNING_KVER=$(uname -r)
            
            if [[ $RUNNING_KVER == *"-cachyos"* ]]; then
                # CachyOS has multiple nested kernel names (bore, deckify, etc.)
                # Try to find headers matching the exact kernel suffix if possible
                local SUFFIX=$(echo "$RUNNING_KVER" | sed 's/^[0-9.]*-[0-9]*-\(.*\)/\1/')
                if [[ -n "$SUFFIX" ]] && pacman -Si "linux-$SUFFIX-headers" &>/dev/null; then
                    HEADERS_PKG="linux-$SUFFIX-headers"
                elif pacman -Si linux-cachyos-headers &>/dev/null; then
                    HEADERS_PKG="linux-cachyos-headers"
                else
                    HEADERS_PKG="linux-headers"
                fi
            elif [[ $RUNNING_KVER == *"-zen"* ]]; then
                HEADERS_PKG="linux-zen-headers"
            elif [[ $RUNNING_KVER == *"-lts"* ]]; then
                HEADERS_PKG="linux-lts-headers"
            elif [[ $RUNNING_KVER == *"-hardened"* ]]; then
                HEADERS_PKG="linux-hardened-headers"
            elif [[ $RUNNING_KVER == *"-rt"* ]]; then
                HEADERS_PKG="linux-rt-headers"
            else
                HEADERS_PKG="linux-headers"
            fi
            
            info "Attempting to install: dkms $HEADERS_PKG base-devel"
            if ! pacman -S --needed --noconfirm dkms "$HEADERS_PKG" base-devel; then
                warn "Could not install $HEADERS_PKG. Trying generic linux-headers..."
                pacman -S --needed --noconfirm dkms linux-headers base-devel || warn "Header installation failed. DKMS might not work without headers."
            fi
            ;;
        opensuse*|suse*)
            info "Installing dependencies (zypper)..."
            zypper install -y dkms kernel-devel kernel-default-devel gcc make
            ;;
        void)
            info "Installing dependencies (xbps)..."
            xbps-install -Sy dkms linux-headers base-devel
            ;;
        gentoo)
            info "Gentoo detected. Ensure sys-kernel/dkms and linux-headers are installed."
            command -v dkms &>/dev/null || error "dkms not found. Install it with: emerge sys-kernel/dkms"
            ;;
        *)
            # Try ID_LIKE as fallback
            case "$DISTRO_LIKE" in
                *debian*|*ubuntu*)
                    info "Debian-like distro detected, using apt..."
                    apt-get update -qq
                    apt-get install -y dkms build-essential linux-headers-"$(uname -r)"
                    ;;
                *fedora*|*rhel*)
                    info "Fedora-like distro detected, using dnf..."
                    dnf install -y dkms kernel-devel kernel-headers gcc make
                    ;;
                *arch*)
                    info "Arch-like distro detected, using pacman..."
                    pacman -S --needed --noconfirm dkms linux-headers base-devel
                    ;;
                *suse*)
                    info "SUSE-like distro detected, using zypper..."
                    zypper install -y dkms kernel-devel kernel-default-devel gcc make
                    ;;
                *)
                    warn "Unknown distro '${DISTRO_ID}'. Attempting generic install..."
                    warn "Make sure you have installed: dkms, gcc, make, kernel-headers"
                    command -v dkms &>/dev/null || error "dkms not found. Please install it manually."
                    ;;
            esac
            ;;
    esac
}

# ── Install ───────────────────────────────────────────────────────────────────

do_install() {
    [[ $EUID -ne 0 ]] && error "This script must be run as root (use sudo)."

    detect_distro
    install_deps

    # Detect if the running kernel was compiled with Clang and automatically set LLVM=1
    if grep -iq "clang" /proc/version; then
        info "Kernel built with Clang/LLVM detected. Automatically setting LLVM=1 for build..."
        export LLVM=1
    fi

    cd "$SCRIPT_DIR"

    # Remove old DKMS entry if exists
    if dkms status "$MODNAME/$MODVER" 2>/dev/null | grep -q "$MODNAME"; then
        warn "Removing existing DKMS entry ($MODNAME/$MODVER)..."
        dkms remove -m "$MODNAME" -v "$MODVER" --all 2>/dev/null || true
    fi
    rm -rf "/usr/src/${MODNAME}-${MODVER}"
    mkdir -p "/usr/src/${MODNAME}-${MODVER}"

    # Ensure /usr/src directory exists and copy source files
    # Prepare source for DKMS
    cp "$SCRIPT_DIR/dkms.conf" "$SCRIPT_DIR/Makefile" "$SCRIPT_DIR"/*.c "/usr/src/${MODNAME}-${MODVER}/"
    cp "$SCRIPT_DIR"/*.h "/usr/src/${MODNAME}-${MODVER}/" 2>/dev/null || true

    if $STOCK_FAN_SUPPORT; then
        info "Kernel $(uname -r) detected (>= 7.0) — stock hp-wmi already has Omen fan control."
        info "Only building hp-rgb-lighting (RGB keyboard control)..."

        # Create an RGB-only DKMS config in /usr/src
        cat > "/usr/src/${MODNAME}-${MODVER}/dkms.conf" <<DKMSRGB
PACKAGE_NAME="hp-rgb-lighting"
PACKAGE_VERSION="$MODVER"
MAKE[0]="grep -iq clang /proc/version && make LLVM=1 -C \$kernel_source_dir M=\$dkms_tree/\$module/\$module_version/build EXTRA_CFLAGS='' modules || make -C \$kernel_source_dir M=\$dkms_tree/\$module/\$module_version/build EXTRA_CFLAGS='' modules"
CLEAN=true
BUILT_MODULE_NAME[0]="hp-rgb-lighting"
DEST_MODULE_LOCATION[0]="/kernel/drivers/platform/x86/hp"
AUTOINSTALL="yes"
DKMSRGB
    else
        info "Kernel $(uname -r) detected (< 7.0) — installing both hp-wmi and hp-rgb-lighting..."
        
        info "Checking for stock hp-wmi driver to backup and disable..."
        ORIG_WMI=$(modinfo -n hp-wmi 2>/dev/null || true)
        if [[ -n "$ORIG_WMI" ]] && [[ -f "$ORIG_WMI" ]] && [[ ! "$ORIG_WMI" == *"updates"* ]]; then
            info "Backing up stock driver: $ORIG_WMI"
            mv "$ORIG_WMI" "${ORIG_WMI}.backup"
        fi
    fi

    # Install via DKMS
    info "Installing via DKMS..."
    if ! dkms status "$MODNAME/$MODVER" 2>/dev/null | grep -q "added"; then
        dkms add -m "$MODNAME" -v "$MODVER" || true
    fi
    dkms build -m "$MODNAME" -v "$MODVER" || error "DKMS build failed. Check logs."
    dkms install -m "$MODNAME" -v "$MODVER" --force || error "DKMS install failed."

    # ── Secure Boot check ───────────────────────────────────────────────────────
    SECUREBOOT=false
    if command -v mokutil &>/dev/null; then
        if mokutil --sb-state 2>/dev/null | grep -qi "SecureBoot enabled"; then
            SECUREBOOT=true
        fi
    fi

    if $SECUREBOOT; then
        # 1. Generate MOK Key (if it doesn't exist)
        MOK_DIR="/var/lib/hp-manager/mok"
        mkdir -p "$MOK_DIR"
        if [ ! -f "$MOK_DIR/MOK.priv" ] || [ ! -f "$MOK_DIR/MOK.der" ]; then
            info "Generating MOK key for Secure Boot..."
            openssl req -new -x509 -newkey rsa:2048 -keyout "$MOK_DIR/MOK.priv" -outform DER -out "$MOK_DIR/MOK.der" -days 36500 -subj "/CN=hp-manager-mok/" -nodes 2>/dev/null
        fi

        # 2. Sign installed modules
        KVER=$(uname -r)
        info "Signing custom modules for Secure Boot..."
        SIGN_SCRIPT=$(find /usr/src/linux-headers-$KVER/scripts /usr/src/kernels/$KVER/scripts /lib/modules/$KVER/build/scripts -name "sign-file" -type f 2>/dev/null | head -n 1)
        
        if [ -n "$SIGN_SCRIPT" ]; then
            for MOD_NAME in "hp-rgb-lighting.ko" "hp-wmi.ko"; do
                if [ "$MOD_NAME" = "hp-wmi.ko" ] && $STOCK_FAN_SUPPORT; then
                    continue # We use stock hp-wmi, no need to sign a custom one
                fi
                # Find the module file installed by us (not the backups)
                MOD_PATH=$(find /lib/modules/$KVER -name "$MOD_NAME" 2>/dev/null | grep -v "backup" | head -n 1)
                if [ -n "$MOD_PATH" ]; then
                    "$SIGN_SCRIPT" sha256 "$MOK_DIR/MOK.priv" "$MOK_DIR/MOK.der" "$MOD_PATH" || warn "Failed to sign $MOD_NAME"
                fi
            done
        else
            warn "sign-file script not found! The modules could not be signed. Secure Boot may block them."
        fi

        # 3. Import MOK to EFI if not enrolled
        if mokutil --test-key "$MOK_DIR/MOK.der" 2>/dev/null | grep -qi "not enrolled"; then
            info "Enrolling MOK key..."
            printf "yunusemreyl\nyunusemreyl\n" | mokutil --import "$MOK_DIR/MOK.der" 2>/dev/null || warn "Failed to import MOK key."
            
            echo ""
            echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
            echo -e "${YELLOW}║  🔒 Secure Boot is ENABLED                                ║${NC}"
            echo -e "${YELLOW}║                                                           ║${NC}"
            echo -e "${YELLOW}║  A Machine Owner Key (MOK) has been registered to sign    ║${NC}"
            echo -e "${YELLOW}║  the custom drivers.                                      ║${NC}"
            echo -e "${YELLOW}║                                                           ║${NC}"
            echo -e "${YELLOW}║  ${RED}PLEASE REBOOT YOUR SYSTEM NOW.${YELLOW}                           ║${NC}"
            echo -e "${YELLOW}║  Upon reboot, a blue 'Perform MOK management' screen      ║${NC}"
            echo -e "${YELLOW}║  will appear. Follow these exact steps:                   ║${NC}"
            echo -e "${YELLOW}║                                                           ║${NC}"
            echo -e "${YELLOW}║  1. Select 'Enroll MOK'                                   ║${NC}"
            echo -e "${YELLOW}║  2. Select 'Continue'                                     ║${NC}"
            echo -e "${YELLOW}║  3. Select 'Yes'                                          ║${NC}"
            echo -e "${YELLOW}║  4. Enter password: ${GREEN}yunusemreyl${YELLOW}                           ║${NC}"
            echo -e "${YELLOW}║  5. Select 'Reboot'                                       ║${NC}"
            echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
            echo ""
            warn "Skipping module load. The modules will load automatically after MOK enrollment."
        else
            ok "MOK key is already enrolled. Modules can be loaded."
        fi
    fi

    # Load the modules
    MOK_PENDING=false
    if $SECUREBOOT && mokutil --test-key "$MOK_DIR/MOK.der" 2>/dev/null | grep -qi "not enrolled"; then
        MOK_PENDING=true
    fi

    if $MOK_PENDING; then
        info "MOK enrollment pending — skipping module load until reboot."
    elif $STOCK_FAN_SUPPORT; then
        info "Loading modules..."
        # Only load hp-rgb-lighting; fan control uses stock hp-wmi
        modprobe led_class_multicolor 2>/dev/null || true
        if ! modprobe hp_rgb_lighting 2>/dev/null; then
            insmod "$SCRIPT_DIR/hp-rgb-lighting.ko" 2>/dev/null || warn "hp-rgb-lighting could not be loaded. (Secure boot issue?)"
        fi
        ok "hp-rgb-lighting (RGB) installed. Stock hp-wmi handles fan control."
    else
        info "Loading modules..."
        rmmod hp_wmi 2>/dev/null || true
        modprobe led_class_multicolor 2>/dev/null || true
        if ! modprobe hp_wmi 2>/dev/null; then
            insmod "$SCRIPT_DIR/hp-wmi.ko" || warn "hp-wmi could not be loaded."
        fi
        if ! modprobe hp_rgb_lighting 2>/dev/null; then
            insmod "$SCRIPT_DIR/hp-rgb-lighting.ko" 2>/dev/null || warn "hp-rgb-lighting could not be loaded."
        fi
        ok "Both hp-wmi and hp-rgb-lighting installed."
    fi

    echo ""
    info "The module will be automatically rebuilt on kernel updates via DKMS."
    if ! $STOCK_FAN_SUPPORT; then
        info "Fan control: /sys/devices/platform/hp-wmi/hwmon/hwmon*/pwm1_enable"
        info "Fan speed:   /sys/devices/platform/hp-wmi/hwmon/hwmon*/fan*_target"
    fi
    echo ""
}

# ── Uninstall ─────────────────────────────────────────────────────────────────

do_uninstall() {
    [[ $EUID -ne 0 ]] && error "This script must be run as root (use sudo)."

    info "Unloading modules..."
    rmmod hp_wmi 2>/dev/null || true
    rmmod hp_rgb_lighting 2>/dev/null || true

    info "Removing DKMS entry..."
    if dkms status "$MODNAME/$MODVER" 2>/dev/null | grep -q "$MODNAME"; then
        dkms remove -m "$MODNAME" -v "$MODVER" --all
        rm -rf "/usr/src/${MODNAME}-${MODVER}"
        ok "Uninstalled successfully."
    else
        warn "DKMS entry not found. Nothing to remove."
    fi

    # Restore original driver if backup exists
    info "Restoring original driver backups (if any)..."
    KVER=$(uname -r)
    FOUND_BACKUP=false
    for BU_FILE in $(find /lib/modules/"$KVER" -name "hp-wmi.ko*.backup" 2>/dev/null); do
        ORIG_FILE="${BU_FILE%.backup}"
        info "Restoring $ORIG_FILE from backup..."
        mv "$BU_FILE" "$ORIG_FILE"
        FOUND_BACKUP=true
    done

    if [ "$FOUND_BACKUP" = true ]; then
        depmod -a
    fi

    # Reload original kernel module
    info "Reloading original hp-wmi module..."
    modprobe hp_wmi 2>/dev/null || warn "Could not reload original hp-wmi module."
}

# ── Main ──────────────────────────────────────────────────────────────────────

usage() {
    echo "Usage: sudo $0 [install|uninstall]"
    echo ""
    echo "  install     Build and install the module via DKMS"
    echo "  uninstall   Remove the module and restore the original"
    echo ""
    echo "If no argument is given, 'install' is assumed."
}

case "${1:-install}" in
    install)   do_install ;;
    uninstall) do_uninstall ;;
    -h|--help) usage ;;
    *)         usage; exit 1 ;;
esac
