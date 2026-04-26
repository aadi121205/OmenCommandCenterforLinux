#!/usr/bin/env python3
"""
Centralized i18n module for OMEN Command Center for Linux.
This module is imported by all pages — never run as __main__,
so there's only one copy of active_lang in memory.
"""

active_lang = "en"

TRANSLATIONS = {
    "en": {
        # Nav
        "fan": "Performance",
        "lighting": "Lighting", "mux": "MUX", "settings": "Settings",
        "keyboard": "Shortcuts",
        # Fan page
        "fan_control": "Fan Control", "system_status": "SYSTEM STATUS",
        "power_profile": "POWER PROFILE", "fan_mode": "FAN MODE",
        "fan_curve": "FAN CURVE", "all_sensors": "All Sensors",
        "fan_disabled": "Fan control unavailable",
        "checking": "Checking...", "no_ppd": "No PPD",
        "active_profile": "Active profile", "mode": "Mode",
        "saver": "Power Saver", "balanced": "Balanced", "performance": "Performance",
        "auto": "Automatic", "max": "Maximum", "custom": "Custom", "standard": "Standard",
        "curve_desc": "Drag points to customize fan curve. X: Temperature (°C), Y: Fan Speed (%)",
        "no_sensor": "No sensor data found",
        # Lighting page
        "keyboard_lighting": "Keyboard Lighting", "keyboard_light": "KEYBOARD LIGHT",
        "zone": "Zone", "all_zones": "All",
        "effect": "EFFECT", "direction": "DIRECTION", "speed": "SPEED", "brightness": "BRIGHTNESS",
        "static_eff": "Static", "breathing": "Breathing", "wave": "Wave", "cycle": "Cycle",
        "ltr": "Left → Right", "rtl": "Right → Left",
        "win_lock": "Gaming Key Lock",
        # Keyboard page
        "keyboard_shortcuts": "Shortcuts", "special_keys": "SPECIAL KEYS",
        "omen_key": "Omen Key", "victus_key": "Omen Key",
        "calc_key": "Calculator Key", "prt_sc_fix": "Fix Print Screen (PrtSc)",
        "prt_sc_desc": "Makes PrtSc key work as real Print Screen instead of triggering Screenshot Tool.",
        "f1_fix": "Fix F1 (Presentation) Key",
        "f1_desc": "Makes F1 key work as standard F1 instead of Super+P (Presentation mode).",
        "apply_shortcuts": "Apply Changes",
        "shortcuts_desc": "You can permanently change the behavior of certain keys on your laptop here.",
        "hwdb_applied": "Keyboard fixes have been applied successfully.",
        # MUX page
        "mux_switch": "MUX Switch", "gpu_info": "GPU INFO",
        "gpu_card": "Graphics Card", "driver_ver": "Driver Version",
        "gpu_mode": "GPU MODE", "hybrid": "Hybrid", "discrete": "Discrete GPU",
        "integrated": "Integrated GPU",
        "hybrid_desc": "NVIDIA Optimus (Hybrid)", "discrete_desc": "NVIDIA GeForce RTX",
        "integrated_desc": "Intel Iris Xe / AMD Radeon Graphics",
        "gpu_checking": "Checking GPU mode...",
        "restart_warn": "System restart required to change GPU mode.",
        "mux_not_found": "MUX tool not found",
        "mux_install_hint": "envycontrol, supergfxctl or prime-select must be installed.",
        "restart": "Restart",
        "restart_confirm": "System will restart to change GPU mode to '{mode}'. Continue?",
        "mode_set": "Mode set to '{mode}'. Restarting...",
        "mux_backend_label": "MUX Backend Tool", "mux_auto": "Auto Detect",
        # Settings page
        "appearance": "APPEARANCE", "theme": "Theme", "lang_label": "Language",
        "dark": "Dark", "light": "Light", "system": "System Default",
        "updates": "UPDATES", "current_ver": "Current version",
        # Dashboard
        "dashboard": "Dashboard", "quick_status": "Quick Status",
        "hardware_profile": "Hardware Profile", "resources": "Resources",
        "quick_actions": "Quick Actions", "clean_memory": "Clean Memory",
        "max_fan": "MAX Fan", "eco_mode": "Eco Mode",
        "go_performance": "Go to Performance",
        "fan_metric": "Fan",
        "disk": "Disk", "ram": "RAM",
        "cpu_load_30s": "CPU Load (Last 30s)",
        "power_profile_label": "Power Profile", "fan_mode_label": "Fan Mode",
        "gpu_mux_label": "GPU / MUX",
        "battery": "Battery", "ac_power": "Power Cable",
        "health": "Health",
        "power_saver_lbl": "Power Saver",
        "balanced_lbl": "Balanced", "performance_lbl": "Performance",
        "check_update": "Check for Updates", "download": "Download",
        "sys_info": "SYSTEM INFO",
        "computer": "Computer", "kernel": "Kernel",
        "os_name": "Operating System", "arch": "Architecture",
        "driver_status": "DRIVER STATUS",
        "loaded": "✓ Loaded", "not_loaded": "✗ Not Loaded",
        "developer": "Developer",
        "home_subtitle": "Choose a module to continue",
        "debug_info_title": "Diagnostic and Debug",
        "show_debug_info": "Show Debug Info",
        "copy_debug_log": "Copy Debug Info",
        "copied_to_clipboard": "Copied to clipboard",
        "debug_console_title": "System Diagnostic Console",
        "debug_collecting": "Gathering system information...\nConnecting to WMI...\nReading DMI tables...\nAnalyzing kernel logs...\n\nPlease wait...",
        "disclaimer": "This tool has no official affiliation with <b>Hewlett Packard</b>.",
        "update_checking": "Checking...",
        "new_ver_available": "New version available",
        "up_to_date": "Up to date", "conn_failed": "Connection failed",
        "error": "Error",
        "install_update": "Install Update",
        "downloading_update": "Downloading...",
        "installing_update": "Installing...",
        "update_success": "Update installed successfully! Please restart the application.",
        "update_failed": "Update failed",
        "restart_app": "Restart Application",

        # Temperature unit
        "temp_unit": "Temperature Unit", "celsius": "Celsius (°C)", "fahrenheit": "Fahrenheit (°F)",
        # Fan curve widget
        "temp_axis": "Temperature (°C)", "fan_speed_axis": "Fan Speed (%)",
        # Sensor categories
        "other_sensors": "Other",
        # Profile tooltips
        "saver_tooltip": "Maximum battery life with reduced power limits.",
        "balanced_tooltip": "Balance between power and efficiency.",
        "performance_tooltip": "Remove all power limits for maximum performance.",
        "power_managed_by": "Power mode is managed by {tool}.",
    },
}


def T(key):
    """Get translation for key."""
    return TRANSLATIONS["en"].get(key, key)


def set_lang(lang):
    """No-op: language is fixed to English."""
    pass


def get_lang():
    """Get the current active language."""
    return "en"
