#!/usr/bin/env python3
"""Keyboard glow preview widget using Cairo."""
import math, time, colorsys, cairo, os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Pango, PangoCairo, GLib

# Fix path to images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check relative to source (3 levels up)
IMG_SRC = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "images"))

# Check relative to installed location (2 levels up)
IMG_INSTALLED = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "images"))

if os.path.exists(os.path.join(IMG_SRC, "keyboard.png")):
    IMAGES_DIR = IMG_SRC
elif os.path.exists(os.path.join(IMG_INSTALLED, "keyboard.png")):
    IMAGES_DIR = IMG_INSTALLED
else:
    # Final fallback
    IMAGES_DIR = "/usr/share/hp-manager/images"


class KeyboardPreview(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(600, 240)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.power = True
        self.mode = "static"
        self.speed = 50
        self.brightness = 100
        self.direction = "ltr"
        self.zone_colors = [(0.1, 0.1, 0.1)] * 8  # RGBA floats
        self.set_draw_func(self._draw)
        self._anim_timer = None
        
        # Load background image
        self.bg_surf = None
        img_path = os.path.join(IMAGES_DIR, "keyboard.png")
        if os.path.exists(img_path):
            try:
                self.bg_surf = cairo.ImageSurface.create_from_png(img_path)
            except Exception as e:
                print(f"Failed to load keyboard image: {e}")

    def _anim_tick(self):
        if self.power and self.mode != "static":
            self.queue_draw()
        return True

    def resume_animation(self):
        if not self._anim_timer:
            self._anim_timer = GLib.timeout_add(33, self._anim_tick)

    def pause_animation(self):
        if self._anim_timer:
            GLib.source_remove(self._anim_timer)
            self._anim_timer = None

    def set_zone_color(self, zone, r, g, b, redraw=True):
        if 0 <= zone < 8:
            self.zone_colors[zone] = (r, g, b)
        if redraw:
            self.queue_draw()

    def set_all_zones(self, r, g, b):
        self.zone_colors = [(r, g, b)] * 8
        self.queue_draw()

    def _draw(self, _, cr, w, h):
        if w <= 0 or h <= 0:
            return
            
        # 1. Draw Background Image (scaled to fit drawing area)
        if self.bg_surf is not None:
            img_w: float = float(self.bg_surf.get_width())
            img_h: float = float(self.bg_surf.get_height())
            scale_x = w / img_w
            scale_y = h / img_h
            scale = min(scale_x, scale_y)
            if scale <= 0.0001: return
            x_off = (w - (img_w * scale)) / 2
            y_off = (h - (img_h * scale)) / 2
            
            drawn_w = img_w * scale
            drawn_h = img_h * scale
            
            cr.save()
            cr.translate(x_off, y_off)
            cr.scale(scale, scale)
            cr.set_source_surface(self.bg_surf, 0, 0)
            cr.paint()
            cr.restore()
        else:
            x_off, y_off = 0, 0
            drawn_w, drawn_h = w, h
            # Fallback
            cr.set_source_rgba(0.1, 0.1, 0.1, 1)
            self._rounded_rect(cr, 0, 0, w, h, 16)
            cr.fill()

        if not self.power:
            # Dim if off
            cr.set_source_rgba(0, 0, 0, 0.6)
            cr.paint()
            return

        # 2. Draw Glow Overlay
        # Use simple ADD for glow effect
        cr.set_operator(cairo.Operator.ADD)
        
        # Approximate key zone centers based on image
        # Zones: Left, WASD/Mid-Left, Mid-Right, Numpad/Right
        centers = [
            (x_off + drawn_w * 0.15, y_off + drawn_h * 0.5), # Zone 1
            (x_off + drawn_w * 0.38, y_off + drawn_h * 0.5), # Zone 2
            (x_off + drawn_w * 0.62, y_off + drawn_h * 0.5), # Zone 3
            (x_off + drawn_w * 0.85, y_off + drawn_h * 0.5)  # Zone 4
        ]

        now = time.time()
        
        # Determine actual zone colors based on mode
        actual_colors = [self.zone_colors[i] for i in range(4)]
        
        if not self.power:
            # Everything off
            actual_colors = [(0, 0, 0) for _ in range(8)]
        else:
            spd = float(self.speed)
            
            if self.mode == "breathing":
                # Matches daemon: period = 8.0 - (spd * 0.06)
                period = 8.0 - (spd * 0.06)
                phase = 0.1 + 0.9 * ((math.sin(2 * math.pi * now / period) + 1) / 2)
                actual_colors = [(r*phase, g*phase, b*phase) for r,g,b in self.zone_colors[:4]]
                
            elif self.mode == "wave":
                # Matches daemon: hue = (t * spd * 0.007 + offset) % 1.0
                for i in range(4):
                    offset = (i * 0.15) if self.direction == "ltr" else ((3 - i) * 0.15)
                    hue = (now * spd * 0.007 + offset) % 1.0
                    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                    actual_colors[i] = (r, g, b)
                    
            elif self.mode == "cycle":
                # Matches daemon: hue = (t * (spd * 0.003)) % 1.0
                hue = (now * (spd * 0.003)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                actual_colors = [(r, g, b) for _ in range(4)]
                
        # Apply global brightness
        bri = self.brightness / 100.0
        actual_colors = [(r*bri, g*bri, b*bri) for r,g,b in actual_colors]

        # Lighting effects behind keys
        if self.power:
            cr.save()
            for i in range(4):
                if sum(actual_colors[i]) > 0:
                    cx, cy = centers[i] # Use the pre-defined center for the zone
                    # Ensure drawn_w is float for multiplication
                    radius: float = float(drawn_w) * 0.25
                    pat = cairo.RadialGradient(cx, cy, 0, cx, cy, radius)
                    pat.add_color_stop_rgba(0, actual_colors[i][0], actual_colors[i][1], actual_colors[i][2], 0.4) # Inner intense
                    pat.add_color_stop_rgba(0.6, actual_colors[i][0], actual_colors[i][1], actual_colors[i][2], 0.1) # Middle soft
                    pat.add_color_stop_rgba(1, actual_colors[i][0], actual_colors[i][1], actual_colors[i][2], 0) # Outer transparent
                    cr.set_source(pat)
                    cr.paint()
            cr.restore()

    def _rounded_rect(self, cr, x, y, w, h, r):
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    def cleanup(self):
        if hasattr(self, '_anim_timer') and self._anim_timer:
            GLib.source_remove(self._anim_timer)
            self._anim_timer = None
