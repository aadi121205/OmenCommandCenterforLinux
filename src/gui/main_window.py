#!/usr/bin/env python3
"""HP RGB Control — GTK4 front-end (RGB only)."""

import sys, os, json, threading

import gi
gi.require_version('Gtk', '4.0')
try:
    gi.require_version('Adw', '1')
    from gi.repository import Adw
    HAS_ADW = True
except ValueError:
    Adw = None
    HAS_ADW = False

from gi.repository import Gtk, Gdk, GLib, Gio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJ_SRC       = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
PROJ_INSTALLED = os.path.abspath(os.path.join(BASE_DIR, ".."))
if os.path.exists(os.path.join(PROJ_SRC, "images", "omenapplogo.png")):
    IMAGES_DIR = os.path.join(PROJ_SRC, "images")
elif os.path.exists(os.path.join(PROJ_INSTALLED, "images", "omenapplogo.png")):
    IMAGES_DIR = os.path.join(PROJ_INSTALLED, "images")
else:
    IMAGES_DIR = "/usr/share/hp-manager/images"

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.dirname(BASE_DIR))

from pages.lighting_page import LightingPage
from i18n import set_lang

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

CONFIG_FILE      = os.path.expanduser("~/.config/hp-manager.toml")
CONFIG_FILE_JSON = os.path.expanduser("~/.config/hp-manager.json")


class HPManagerWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("HP RGB Control")
        self.set_default_size(860, 600)
        self.set_resizable(True)

        display = Gdk.Display.get_default()
        icon_theme = Gtk.IconTheme.get_for_display(display)
        if IMAGES_DIR not in icon_theme.get_search_path():
            icon_theme.add_search_path(IMAGES_DIR)
        self.set_icon_name("omenapplogo")

        self.app_theme = "dark"
        self.service   = None
        self._css_provider = Gtk.CssProvider()

        self._load_config()
        self._apply_theme_preference()
        self._apply_css()

        self.lighting_page = LightingPage(service=None)
        self.set_child(self.lighting_page)

        self.connect("close-request", self._on_close)
        self.connect("notify::default-width", self._on_resize)
        self.connect("notify::default-height", self._on_resize)

        threading.Thread(target=self._connect_daemon, daemon=True).start()

    # ── Daemon connection ─────────────────────────────────────────────────────

    def _connect_daemon(self):
        try:
            from pydbus import SystemBus
            svc = SystemBus().get("com.aadi.hpmanager")
            self.service = svc
            GLib.idle_add(self.lighting_page.set_service, svc)
            print("Daemon connected", flush=True)
        except Exception as e:
            print(f"Daemon connection failed: {e}", flush=True)
            print("Application will run without daemon support.", flush=True)

    # ── Resize ───────────────────────────────────────────────────────────────

    def _on_resize(self, *_):
        w = self.get_width()
        h = self.get_height()
        if w <= 0 or h <= 0:
            return
        if w < 700:
            bucket = "compact"
        elif w > 1200:
            bucket = "spacious"
        else:
            bucket = "normal"
        if hasattr(self.lighting_page, "set_ui_scale"):
            self.lighting_page.set_ui_scale(bucket, w, h)

    # ── Close ─────────────────────────────────────────────────────────────────

    def _on_close(self, *_):
        if hasattr(self.lighting_page, "cleanup"):
            try:
                self.lighting_page.cleanup()
            except Exception:
                pass
        try:
            self.get_application().quit()
        except Exception:
            pass
        return False

    # ── Config ───────────────────────────────────────────────────────────────

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE) and tomllib is not None:
                with open(CONFIG_FILE, "rb") as f:
                    data = tomllib.load(f)
                self.app_theme = data.get("theme", "dark")
            elif os.path.exists(CONFIG_FILE_JSON):
                with open(CONFIG_FILE_JSON) as f:
                    data = json.load(f)
                self.app_theme = data.get("theme", "dark")
        except Exception:
            pass

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            theme = str(self.app_theme).replace('"', '\\"')
            with open(CONFIG_FILE, "w") as f:
                f.write(f'theme = "{theme}"\n')
            with open(CONFIG_FILE_JSON, "w") as f:
                json.dump({"theme": self.app_theme}, f)
        except Exception:
            pass

    # ── Theming ───────────────────────────────────────────────────────────────

    def _apply_theme_preference(self):
        if HAS_ADW:
            sm = Adw.StyleManager.get_default()
            if self.app_theme == "dark":
                sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            elif self.app_theme == "light":
                sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            else:
                sm.set_color_scheme(Adw.ColorScheme.DEFAULT)
            return
        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property(
                "gtk-application-prefer-dark-theme",
                self.app_theme != "light"
            )

    def _is_dark(self):
        if self.app_theme == "dark":
            return True
        if self.app_theme == "light":
            return False
        if HAS_ADW:
            return Adw.StyleManager.get_default().get_dark()
        settings = Gtk.Settings.get_default()
        if settings is not None:
            try:
                return bool(settings.get_property("gtk-application-prefer-dark-theme"))
            except Exception:
                pass
        return True

    @staticmethod
    def _hex_to_rgb(hex_color):
        h = hex_color.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    @staticmethod
    def _lighten(hex_color, amount=30):
        r, g, b = HPManagerWindow._hex_to_rgb(hex_color)
        return f"#{min(255,r+amount):02X}{min(255,g+amount):02X}{min(255,b+amount):02X}"

    @staticmethod
    def _darken(hex_color, amount=30):
        r, g, b = HPManagerWindow._hex_to_rgb(hex_color)
        return f"#{max(0,r-amount):02X}{max(0,g-amount):02X}{max(0,b-amount):02X}"

    def _get_system_accent(self):
        if HAS_ADW:
            try:
                sm = Adw.StyleManager.get_default()
                ac = sm.get_accent_color()
                rgba = ac.to_rgba()
                r = int(rgba.red * 255)
                g = int(rgba.green * 255)
                b = int(rgba.blue * 255)
                if r or g or b:
                    return f"#{r:02X}{g:02X}{b:02X}"
            except Exception:
                pass
        return "#3584e4"

    def _apply_css(self):
        dark = self._is_dark()

        accent       = self._get_system_accent() if not dark else "#3ca8ff"
        accent_hover = self._lighten(accent, 12)
        accent_dark  = self._darken(accent, 60)
        ar, ag, ab   = self._hex_to_rgb(accent)
        accent_dim            = f"rgba({ar},{ag},{ab},0.18)"
        accent_border_hover   = f"rgba({ar},{ag},{ab},0.38)"
        accent_shadow_strong  = "rgba(255,255,255,0.22)"
        surface_radius = 16

        if dark:
            bg          = "#121316"
            card_bg     = "rgba(44,45,50,0.92)"
            card_border = "rgba(220,228,239,0.14)"
            sep_color   = "rgba(255,255,255,0.12)"
            fg          = "#ffffff"
            fg_dim      = "#d0d4dc"
            fg_very_dim = "#9ea6b4"
            input_bg    = "rgba(255,255,255,0.11)"
        else:
            accent       = self._get_system_accent()
            accent_hover = self._darken(accent, 10)
            accent_dark  = self._darken(accent, 60)
            ar, ag, ab   = self._hex_to_rgb(accent)
            accent_dim           = f"rgba({ar},{ag},{ab},0.15)"
            accent_border_hover  = f"rgba({ar},{ag},{ab},0.3)"
            accent_shadow_strong = "rgba(255,255,255,0.18)"
            bg          = "#f0f0f4"
            card_bg     = "rgba(255,255,255,0.78)"
            card_border = "rgba(0,0,0,0.08)"
            sep_color   = "rgba(0,0,0,0.12)"
            fg          = "#121212"
            fg_dim      = "#444444"
            fg_very_dim = "#666666"
            input_bg    = "rgba(0,0,0,0.06)"

        css = f"""
        window {{
            background-color: {bg};
            color: {fg};
            font-family: "Geist", "Inter", "Noto Sans", sans-serif;
        }}

        label {{ color: {fg}; }}
        image {{ color: {fg_dim}; }}
        button label {{ color: inherit; }}

        .heading {{
            color: {fg};
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 0.2px;
        }}
        .title-4 {{
            font-size: 15px;
            font-weight: 700;
            color: {fg};
            font-family: "JetBrains Mono", "Inter", monospace;
        }}
        .dim-label {{
            color: {fg_dim};
            font-size: 12px;
            font-weight: 520;
        }}

        separator {{
            background: {sep_color};
            min-width: 1px;
            min-height: 1px;
        }}

        /* ── Page ── */
        .page-title {{
            font-size: 22px;
            font-weight: 800;
            color: {fg};
            margin-bottom: 5px;
        }}
        .section-title {{
            font-size: 11px;
            font-weight: 700;
            color: {fg_dim};
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}

        /* ── Card ── */
        .card {{
            background-color: {card_bg};
            border: 1px solid {card_border};
            border-radius: {surface_radius}px;
            padding: 28px;
            box-shadow: 0 12px 22px rgba(0,0,0,0.14);
        }}

        /* ── KB frame ── */
        .kb-frame {{
            background: rgba(0,0,0,0.25);
            border: 1px solid {card_border};
            border-radius: {surface_radius}px;
            padding: 12px;
        }}

        /* ── Zone buttons ── */
        .zone-btn {{
            background: {input_bg};
            color: {fg};
            border: 1px solid {card_border};
            border-radius: 20px;
            padding: 8px 16px;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .zone-btn:checked {{
            background: {accent};
            color: white;
            border-color: {accent};
        }}

        /* ── Color picker button ── */
        .color-picker-btn {{
            background: {input_bg};
            border: 2px dashed {fg_very_dim};
            border-radius: 50%;
            min-width: 28px;
            min-height: 28px;
            padding: 0;
            font-weight: 700;
            color: {fg_dim};
        }}

        /* ── Scale / slider ── */
        scale trough {{
            background: {input_bg};
            border-radius: 4px;
        }}
        scale highlight {{
            background: {accent};
            border-radius: 4px;
        }}

        /* ── Dropdown ── */
        dropdown > button {{
            background: rgba(255,255,255,0.04);
            border: 1px solid {card_border};
            outline: none;
            box-shadow: none;
            border-radius: 10px;
            color: {fg};
            min-height: 0;
            padding: 6px 10px;
        }}
        dropdown > button:hover {{
            background: rgba(255,255,255,0.08);
        }}
        dropdown > button:focus {{
            outline: none;
            box-shadow: 0 0 0 2px {accent_dim};
            border: 1px solid {accent_border_hover};
        }}

        /* ── Popover (dropdown list) ── */
        popover, popover.background {{
            background: transparent;
            border: none;
            box-shadow: none;
            color: {fg};
        }}
        popover > contents, popover.background > contents {{
            background: {card_bg};
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px;
            box-shadow: 0 12px 28px rgba(0,0,0,0.24);
            padding: 6px;
        }}
        popover scrolledwindow,
        popover.background scrolledwindow,
        popover viewport,
        popover.background viewport,
        popover listview,
        popover.background listview {{
            background: {card_bg};
            color: {fg};
        }}
        popover modelbutton, popover label {{
            color: {fg};
        }}
        popover row label, popover modelbutton label {{
            color: {fg};
        }}
        popover modelbutton {{
            border-radius: 10px;
            padding: 8px 12px;
            margin: 1px 0;
            font-weight: 600;
            background: transparent;
        }}
        popover modelbutton:hover {{
            background: rgba(255,255,255,0.08);
        }}
        popover row {{
            background: transparent;
            color: {fg};
            border-radius: 10px;
            min-height: 32px;
        }}
        popover row:hover {{
            background: rgba(255,255,255,0.08);
        }}
        popover row:selected {{
            background: {accent_dim};
        }}

        /* ── Switch ── */
        switch:checked {{
            background: {accent};
        }}
        switch slider {{
            border-radius: 999px;
        }}
        """

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        try:
            self._css_provider.load_from_data(css.encode())
        except Exception as e:
            print(f"CSS load error: {e}", flush=True)


# ── Application ───────────────────────────────────────────────────────────────

class HPManagerApp(Adw.Application if HAS_ADW else Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        win = HPManagerWindow(application=app)
        win.present()


def main():
    print("HP RGB Control starting...", flush=True)
    if not HAS_ADW:
        print("Warning: libadwaita not found, running with GTK fallback.", flush=True)
    app = HPManagerApp(
        application_id="com.aadi.hpmanager.gui",
        flags=Gio.ApplicationFlags.FLAGS_NONE,
    )
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
