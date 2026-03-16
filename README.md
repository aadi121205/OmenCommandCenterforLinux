
 # HP Laptop Manager (Linux) v1.1.6 #
<p align="center">
  <img src="images/hplogolight.png" alt="Logo" width="250">

## 📖 About The Project
<p align="center">
  <img src="screenshots/dash.png" alt="Dashboard" width="45%">
  <img src="screenshots/fan.png" alt="Fan Control" width="45%">
</p>
<p align="center">
  <img src="screenshots/key.png" alt="Lighting" width="45%">
  <img src="screenshots/mux.png" alt="MUX Switch" width="45%">
</p>
<p align="center">
  <img src="screenshots/settings.png" alt="Settings" width="45%">
</p>

**HP Laptop Manager** is a native Linux application designed to unlock the full potential of HP Omen and Victus series laptops. It serves as an open-source alternative to the official OMEN Gaming Hub, providing essential controls in a modern, user-friendly interface.

**New in v1.1.6:**

- 🚀 **OMEN 16-wf & 16-ap Support**: Added robust WMI support for OMEN 16 14th Gen and newer models (Board IDs 8C77, 8E35, 8D41).
- 🌪️ **Custom Fan Control Fixes**: Restored and forced manual fan control support (`force_fan_control_support`) specifically for modern boards to enable seamless custom curve tuning.
- 🌡️ **ACPI & Thermal Profile Resolution**: Resolved `AE_AML_BUFFER_LIMIT` crashes by implementing precise RGB write delays, and fixed the "Platform Profile: Not Supported" error by properly aligning the Embedded Controller (EC) thermal offsets. 
- 🌈 **Reversed RGB Layout Engine**: Built an automatic zone-mapping engine to correct the reversed left-to-right keyboard lighting behavior on specific OMEN variants.
- ⚡ **Background Poller Efficiency**: Eliminated UI stuttering and high CPU spikes by shifting all `nvidia-smi` and ACPI sensor polling strictly to non-blocking background threads with backoff cooldowns.

**New in v1.1.5:**

- 🚀 **OMEN 16 (2024) Support**: Added official support for 14th Gen OMEN models (Board ID 8C77).
- 🌪️ **Kernel WMI Fixes**: Resolved the "Query 0x4c error 0x6" issue with advanced thermal fallback and updated custom drivers.
- 📦 **Resource Monitoring**: Redesigned Dashboard gauges to use modern, boxed linear bars for **Disk, RAM, and Battery**.
- 🎹 **Keyboard Shortcuts**: Renamed Keyboard page to "Shortcuts" (Kısayollar) with permanent hardware fixes for PrtSc and F1 keys via `udev`.
- 🧹 **UI Streamlining**: Removed legacy 'Games' and 'Tools' pages to focus on core hardware control and optimize startup performance.
- 🔧 **Diagnostics Upgrade**: Enhanced "Driver Status" and improved debug logging reliability for newer kernel versions.
- 🖼️ **Branding Updates**: Integrated official OMEN/Victus logos and refined technical descriptions for a more premium experience.

**New in v1.1.4:**

- ⚡ **Daemon Optimization**: Optimized core service, reducing CPU usage to ~1%.

**New in v1.1.3:**

- 🎹 **Keyboard Shortcuts & Hardware Fixes**: New dedicated page for OMEN/Victus hotkeys, Windows Key lock (F10), and hardware fixes for PrtSc/F1.
- 🌈 **8-Zone RGB Support**: Expanded lighting control to support high-end OMEN models with 8-zone keyboards.
- 🛠️ **Driver Install Fixes**: Resolved the `cp: target '/usr/src/...' No such file or directory` error and improved DKMS header detection.
- 🔄 **State Restoration**: Windows Key lock and 8-zone colors are now correctly restored after a reboot.

**New in v1.1.2:**

- ⚡ **Interactive Power Manager Selection**: During installation, users can now choose between `power-profiles-daemon`, `ppd-tuned` (recommended for Fedora), `TLP`, or `auto-cpufreq`.
- 🛠️ **Pure DKMS Implementation**: Unified driver installation with pure DKMS support. Redundant manual build steps removed, and robust kernel header detection added for Arch-based (CachyOS, Zen), Fedora, and Debian distros.
- 🔧 **Unified Setup Tool**: Replaced separate `install.sh`, `uninstall.sh`, and `update.sh` with a single, robust `./setup.sh` tool.
- 🔋 **Enhanced Conflict Detection**: Integrated links to TLP and auto-cpufreq repositories for better user guidance during dependency installation.

**New in v1.1.1:**

- 🔋 **TLP / auto-cpufreq Support**: The app now detects if TLP or auto-cpufreq is managing power profiles and gracefully disables the built-in power mode controls with a clear notification on both the Dashboard and Fan pages.
- 🖥️ **GPU MUX Tool Installer**: During installation, if no GPU switching tool (`envycontrol` or `prime-select`) is detected, the installer now offers an interactive menu to install one.
- 🐞 **Debug Information Panel**: A new "Debug Information" section has been added to the Settings page. Users can copy system info (kernel, modules, service status) to the clipboard with one click for easy troubleshooting.
- ⚡ **Performance Optimizations**: Reduced unnecessary `systemctl` calls by caching conflict checks. TLP/auto-cpufreq status is now only polled every ~25-50 seconds instead of every refresh cycle.
- 🔧 **In-App Updater Fix**: The auto-updater now uses `setup.sh update` and a simplified, more robust version comparison algorithm.

**Previous Releases:**

**v1.1.0:**

- ✨ **Name Change**: `hp-omen-core` has been renamed to `hp-rgb-lighting` to better reflect its function and support Victus devices appropriately.
- 🔄 **Kernel 7.0+ Adaptation**: Updated internal checks. Fan control logic defaults to stock `hp-wmi` on kernels >= 7.0, and auto-installs our custom `hp-wmi` module on kernels < 7.0.
- 🚀 **setup.sh update**: Easily adapt to new kernel updates and ensure old `hp-omen-core` debris is purged from your system with one simple update command.

## ✨ Features

### 🎨 RGB Lighting Control
- **4-Zone Control**: Customize colors for different keyboard zones.
- **Effects**: Static, Breathing, Wave, Cycle.
- **Brightness & Speed**: Adjustable parameters for dynamic effects.

### 📊 System Dashboard
- **Real-time Monitoring**: CPU/GPU temperatures and Fan speeds.
- **Performance Profiles**: One-click power profile switching (requires `power-profiles-daemon`).

### 🌪️ Fan Control
- **Standard Mode**: Intelligent software-controlled fan curve for balanced noise/performance.
- **Max Mode**: Forces fans to maximum speed for intensive tasks.
- **Custom Mode**: Drag-and-drop curve editor to create your own fan profiles.

### 🎮 GPU MUX Switch
- Switch between **Hybrid**, **Discrete**, and **Integrated** modes.
- *Note: Requires compatible tools like `envycontrol`, `supergfxctl`, or `prime-select`.*

## 🚀 Installation

### Prerequisites
- A Linux distribution (Ubuntu, Fedora, Arch, OpenSUSE, etc.)
- `git` installed

### Install
Open a terminal and run:

```bash
# Clone the repository
git clone https://github.com/yunusemreyl/LaptopManagerForHP.git
cd LaptopManagerForHP

# Run the installer (requires root)
chmod +x setup.sh
sudo ./setup.sh install
```

The installer will automatically:
1. Detect your package manager and install dependencies.
2. Detect your kernel version and install the appropriate driver:
   - **Kernel ≥ 7.0**: Only installs `hp-rgb-lighting` (RGB). Fan control is provided by the stock `hp-wmi` module.
   - **Kernel < 7.0**: Installs both the custom `hp-wmi` driver (backported) and `hp-rgb-lighting`.
3. Install the daemon and GUI components.
4. Set up system services.
5. Provide a troubleshooting guide if issues occur.

> ⚠️ **Secure Boot Warning**: The `hp-rgb-lighting` kernel module (keyboard RGB control) **cannot be loaded** when Secure Boot is enabled. If you need keyboard lighting control, you must disable Secure Boot from your BIOS settings. Fan control and other features work normally regardless of Secure Boot status on kernel 7.0+.

## 🗑️ Uninstallation

To completely remove the application and its services:

```bash
cd LaptopManagerForHP
sudo ./setup.sh uninstall
```

## 🐧 Compatibility

| Distribution | Status | Notes |
|--------------|--------|-------|
| **Ubuntu 24.04 LTS / Zorin OS / Pop!_OS / Linux Mint** | ✅ Verified | Full support via `apt` |
| **Fedora 42+ / Nobara** | ✅ Verified | Full support via `dnf` |
| **Arch Linux / CachyOS / Manjaro** | ✅ Verified | Full support via `pacman` |
| **OpenSUSE Tumbleweed** | ✅ Verified | Full support via `zypper` |


## 👨‍💻 Credits & Acknowledgments
- **Lead Developer**: [yunusemreyl](https://github.com/yunusemreyl)
- **Contributors**: [ja4e](https://github.com/ja4e)
- **Kernel Module Development**: Special thanks to **[TUXOV](https://github.com/TUXOV/hp-wmi-fan-and-backlight-control)** for the `hp-wmi-fan-and-backlight-control` driver, which makes fan control possible.

## ⚖️ Legal Disclaimer
This tool is an independent open-source project developed by **yunusemreyl**.
It is **NOT** affiliated with or endorsed by **Hewlett-Packard (HP)**.
The software is provided “as is”, without warranty of any kind.

---
*Developed with ❤️ by yunusemreyl*
