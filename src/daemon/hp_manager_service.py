#!/usr/bin/env python3
"""HP RGB Control — D-Bus Daemon (RGB only).
Runs as root to provide keyboard lighting access.
"""
import sys, os, time, threading, logging, json, copy, colorsys, math, glob, re, typing, random

from gi.repository import GLib
from pydbus import SystemBus

# --- PATHS ---
DRIVER_PATH_CUSTOM = "/sys/devices/platform/hp-rgb-lighting"
CONFIG_FILE = "/etc/hp-manager/state.json"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hp-manager")

lock = threading.RLock()
state_changed = threading.Event()
HEX_COLOR_RE = re.compile(r"^[0-9A-F]{6}$")
VALID_LIGHT_MODES = {"static", "breathing", "cycle", "wave", "pulse", "chase", "comet", "twinkle"}
VALID_DIRECTIONS  = {"ltr", "rtl"}


# ============================================================
# RGB CONTROLLER
# ============================================================
class RGBController:
    def __init__(self):
        self.driver_path = self._find_rgb_path()
        self.available = self.driver_path is not None
        self.last_written = [None] * 8
        self.reversed = True
        self._fds = {}
        if self.available:
            for i in range(8):
                try:
                    self._fds[i] = open(f"{self.driver_path}/zone{i}", "w")
                except Exception:
                    pass

    def _find_rgb_path(self):
        if os.path.exists(DRIVER_PATH_CUSTOM):
            logger.info(f"RGB: Using custom driver path {DRIVER_PATH_CUSTOM}")
            return DRIVER_PATH_CUSTOM

        try:
            with open("/proc/modules") as f:
                loaded = f.read()
            if "hp_rgb_lighting" in loaded:
                for candidate in ("/sys/devices/platform/hp-rgb-lighting",
                                  "/sys/devices/platform/hp_rgb_lighting"):
                    if os.path.exists(candidate):
                        logger.info(f"RGB: Found loaded module at {candidate}")
                        return candidate
        except Exception:
            pass

        logger.info("RGB: No RGB control path found (hp-rgb-lighting not loaded)")
        return None

    def is_available(self):
        return self.available

    def write_zone(self, zone, hex_color):
        if not self.available or not (0 <= zone <= 7):
            return

        target_zone = zone
        if self.reversed and 0 <= zone <= 3:
            target_zone = 3 - zone

        if self.last_written[target_zone] == hex_color:
            return

        try:
            time.sleep(0.001)
            fd = self._fds.get(target_zone)
            if fd:
                fd.seek(0)
                fd.write(hex_color)
                fd.flush()
            else:
                with open(f"{self.driver_path}/zone{target_zone}", "w") as f:
                    f.write(hex_color)
            self.last_written[target_zone] = hex_color
        except Exception:
            try:
                with open(f"{self.driver_path}/zone{target_zone}", "w") as f:
                    f.write(hex_color)
                self.last_written[target_zone] = hex_color
                old = self._fds.pop(target_zone, None)
                if old:
                    try: old.close()
                    except Exception: pass
                self._fds[target_zone] = open(f"{self.driver_path}/zone{target_zone}", "w")
            except Exception:
                pass

    def write_all(self, hex_list):
        for i, hc in enumerate(hex_list[:8]):
            self.write_zone(i, hc)

    def write_brightness(self, on):
        if not self.available:
            return
        try:
            with open(f"{self.driver_path}/brightness", "w") as f:
                f.write("1" if on else "0")
                f.flush()
        except Exception:
            pass

    def write_win_lock(self, locked):
        if not self.available:
            return
        try:
            with open(f"{self.driver_path}/win_lock", "w") as f:
                f.write("1" if locked else "0")
                f.flush()
        except Exception:
            pass


# ============================================================
# ANIMATION ENGINE
# ============================================================
class AnimationEngine(threading.Thread):
    FRAME_TIME       = 0.12
    FRAME_TIME_WAVE  = 0.15
    FRAME_TIME_SLOW  = 0.12
    _COLOR_THRESHOLD = 3

    def __init__(self, rgb_ctrl):
        super().__init__(daemon=True)
        self.rgb = rgb_ctrl
        self.running = True
        self._last_uniform: tuple = (-1, -1, -1)
        self._last_wave: typing.List[typing.Tuple[int, int, int]] = [(-1, -1, -1)] * 8
        # Twinkle per-zone state
        self._twinkle_next:   typing.List[float] = [0.0] * 8
        self._twinkle_start:  typing.List[float] = [0.0] * 8
        self._twinkle_dur:    typing.List[float] = [0.3] * 8
        self._twinkle_cols:   typing.List[typing.Tuple[int,int,int]] = [(255, 0, 0)] * 8
        self._twinkle_active: typing.List[bool]  = [False] * 8

    def _uniform_changed(self, new: tuple) -> bool:
        return any(abs(n - o) > self._COLOR_THRESHOLD
                   for n, o in zip(new, self._last_uniform))

    def _zone_changed(self, new: tuple, old: tuple) -> bool:
        return any(abs(n - o) > self._COLOR_THRESHOLD
                   for n, o in zip(new, old))

    def run(self):
        logger.info("Animation engine started")
        while self.running:
            loop_start = time.time()
            with lock:
                pwr  = bool(state.get("power", True))
                mode = str(state.get("mode", "static"))
                bri  = float(state.get("brightness", 100)) / 100.0
                spd  = float(state.get("speed", 50))
                cols = [str(c) for c in state.get("colors", ["FF0000"] * 8)]
                d    = str(state.get("direction", "ltr"))

            if not pwr:
                self.rgb.write_brightness(False)
                self.rgb.write_all(["000000"] * 8)
                self._last_uniform = (-1, -1, -1)
                self._last_wave = [(-1, -1, -1)] * 8
                state_changed.clear()
                state_changed.wait()
                continue

            self.rgb.write_brightness(True)
            t = time.time()

            if mode == "static":
                targets = [self._hex_to_rgb(c) for c in cols]
                self.rgb.write_all([
                    f"{int(r * bri):02X}{int(g * bri):02X}{int(b * bri):02X}"
                    for r, g, b in targets
                ])
                self._last_uniform = (-1, -1, -1)
                self._last_wave = [(-1, -1, -1)] * 8
                state_changed.clear()
                state_changed.wait()
                continue

            elif mode == "breathing":
                period = 8.0 - (spd * 0.06)
                phase  = 0.1 + 0.9 * ((math.sin(2 * math.pi * t / period) + 1) / 2)
                base   = self._hex_to_rgb(cols[0])
                new_color = (
                    int(base[0] * phase * bri),
                    int(base[1] * phase * bri),
                    int(base[2] * phase * bri),
                )
                if self._uniform_changed(new_color):
                    self._last_uniform = new_color
                    hx = f"{new_color[0]:02X}{new_color[1]:02X}{new_color[2]:02X}"
                    self.rgb.write_all([hx] * 8)
                self._last_wave = [(-1, -1, -1)] * 8
                sleep_time = max(self.FRAME_TIME_SLOW - (time.time() - loop_start), 0.001)
                if state_changed.wait(timeout=sleep_time):
                    state_changed.clear()
                continue

            elif mode == "cycle":
                hue = (t * (spd * 0.003)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, bri)
                new_color = (int(r * 255), int(g * 255), int(b * 255))
                if self._uniform_changed(new_color):
                    self._last_uniform = new_color
                    hx = f"{new_color[0]:02X}{new_color[1]:02X}{new_color[2]:02X}"
                    self.rgb.write_all([hx] * 8)
                self._last_wave = [(-1, -1, -1)] * 8
                sleep_time = max(self.FRAME_TIME_SLOW - (time.time() - loop_start), 0.001)
                if state_changed.wait(timeout=sleep_time):
                    state_changed.clear()
                continue

            elif mode == "wave":
                base_cols = [self._hex_to_rgb(c) for c in cols[:4]]
                if not base_cols:
                    base_cols = [(255, 0, 0)]
                while len(base_cols) < 4:
                    base_cols.append(base_cols[-1])

                step_period = max(0.06, 0.42 - (spd * 0.0036))
                shift_pos = t / step_period
                shift_int = int(shift_pos)
                shift_frac = shift_pos - shift_int

                for i in range(8):
                    zone = i if d == "ltr" else (7 - i)
                    idx = (zone + shift_int) % 4
                    nxt = (idx + 1) % 4

                    c0 = base_cols[idx]
                    c1 = base_cols[nxt]

                    r = int((c0[0] + (c1[0] - c0[0]) * shift_frac) * bri)
                    g = int((c0[1] + (c1[1] - c0[1]) * shift_frac) * bri)
                    b = int((c0[2] + (c1[2] - c0[2]) * shift_frac) * bri)
                    new_color = (r, g, b)

                    if self._zone_changed(new_color, self._last_wave[i]):
                        self._last_wave[i] = new_color
                        self.rgb.write_zone(i, f"{new_color[0]:02X}{new_color[1]:02X}{new_color[2]:02X}")
                self._last_uniform = (-1, -1, -1)
                sleep_time = max(self.FRAME_TIME_WAVE - (time.time() - loop_start), 0.001)
                if state_changed.wait(timeout=sleep_time):
                    state_changed.clear()
                continue

            elif mode == "pulse":
                # Each zone breathes with a 90° phase offset — rolling wave of breathing
                period = max(1.0, 7.0 - (spd * 0.05))
                for i in range(8):
                    pos = i if d == "ltr" else (7 - i)
                    phase_off = (pos % 4) * (math.pi / 2)
                    phase = 0.1 + 0.9 * ((math.sin(2 * math.pi * t / period + phase_off) + 1) / 2)
                    base = self._hex_to_rgb(cols[pos % len(cols)])
                    r = int(base[0] * phase * bri)
                    g = int(base[1] * phase * bri)
                    b = int(base[2] * phase * bri)
                    new_c = (r, g, b)
                    if self._zone_changed(new_c, self._last_wave[i]):
                        self._last_wave[i] = new_c
                        self.rgb.write_zone(i, f"{r:02X}{g:02X}{b:02X}")
                self._last_uniform = (-1, -1, -1)
                sleep_time = max(self.FRAME_TIME_SLOW - (time.time() - loop_start), 0.001)
                if state_changed.wait(timeout=sleep_time):
                    state_changed.clear()
                continue

            elif mode == "chase":
                # Single lit zone (with fading trail) bounces left ↔ right
                period = max(0.3, 2.5 - (spd * 0.02))
                t_phase = (t / period) % 2.0
                lead = (t_phase * 3.0) if t_phase <= 1.0 else ((2.0 - t_phase) * 3.0)
                base = self._hex_to_rgb(cols[0])
                for i in range(8):
                    if i >= 4:
                        new_c = (0, 0, 0)
                    else:
                        pos = float(i) if d == "ltr" else float(3 - i)
                        dist = abs(pos - lead)
                        if dist < 0.5:
                            fac = bri
                        elif dist < 1.5:
                            fac = bri * max(0.0, 1.0 - dist)
                        else:
                            fac = 0.0
                        r = int(base[0] * fac)
                        g = int(base[1] * fac)
                        b = int(base[2] * fac)
                        new_c = (r, g, b)
                    if self._zone_changed(new_c, self._last_wave[i]):
                        self._last_wave[i] = new_c
                        rc, gc, bc = new_c
                        self.rgb.write_zone(i, f"{rc:02X}{gc:02X}{bc:02X}")
                self._last_uniform = (-1, -1, -1)
                sleep_time = max(self.FRAME_TIME_WAVE - (time.time() - loop_start), 0.001)
                if state_changed.wait(timeout=sleep_time):
                    state_changed.clear()
                continue

            elif mode == "comet":
                # Bright head + fading trail loops continuously across all 8 zones
                sweep_period = max(0.2, 2.0 - (spd * 0.016))
                pos = (t / sweep_period) % 8.0
                if d == "rtl":
                    pos = (8.0 - pos) % 8.0
                base = self._hex_to_rgb(cols[0])
                for i in range(8):
                    behind = (i - pos) % 8.0
                    if behind < 1.0:
                        fac = bri
                    elif behind < 3.0:
                        fac = bri * (1.0 - (behind - 1.0) / 2.0) * 0.55
                    else:
                        fac = 0.0
                    r = int(base[0] * fac)
                    g = int(base[1] * fac)
                    b = int(base[2] * fac)
                    new_c = (r, g, b)
                    if self._zone_changed(new_c, self._last_wave[i]):
                        self._last_wave[i] = new_c
                        self.rgb.write_zone(i, f"{r:02X}{g:02X}{b:02X}")
                self._last_uniform = (-1, -1, -1)
                sleep_time = max(self.FRAME_TIME_WAVE - (time.time() - loop_start), 0.001)
                if state_changed.wait(timeout=sleep_time):
                    state_changed.clear()
                continue

            elif mode == "twinkle":
                # Zones independently sparkle with random colors
                now = time.time()
                for i in range(8):
                    if not self._twinkle_active[i] and now >= self._twinkle_next[i]:
                        self._twinkle_active[i] = True
                        self._twinkle_start[i]  = now
                        hue = random.random()
                        rc2, gc2, bc2 = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                        self._twinkle_cols[i] = (int(rc2 * 255), int(gc2 * 255), int(bc2 * 255))
                        self._twinkle_dur[i]  = 0.12 + random.random() * 0.3

                    if self._twinkle_active[i]:
                        elapsed = now - self._twinkle_start[i]
                        dur = self._twinkle_dur[i]
                        if elapsed >= dur:
                            self._twinkle_active[i] = False
                            rest = max(0.05, (1.8 - spd * 0.015)) * (0.3 + random.random() * 1.5)
                            self._twinkle_next[i] = now + rest
                            r2, g2, b2 = 0, 0, 0
                        else:
                            progress = elapsed / dur
                            fac = (1.0 - abs(progress * 2.0 - 1.0)) * bri
                            tc = self._twinkle_cols[i]
                            r2 = int(tc[0] * fac)
                            g2 = int(tc[1] * fac)
                            b2 = int(tc[2] * fac)
                    else:
                        r2, g2, b2 = 0, 0, 0

                    new_c = (r2, g2, b2)
                    if self._zone_changed(new_c, self._last_wave[i]):
                        self._last_wave[i] = new_c
                        self.rgb.write_zone(i, f"{r2:02X}{g2:02X}{b2:02X}")
                self._last_uniform = (-1, -1, -1)
                sleep_time = max(self.FRAME_TIME_SLOW - (time.time() - loop_start), 0.001)
                if state_changed.wait(timeout=sleep_time):
                    state_changed.clear()
                continue

            sleep_time = max(self.FRAME_TIME - (time.time() - loop_start), 0.001)
            if state_changed.wait(timeout=sleep_time):
                state_changed.clear()

    def _hex_to_rgb(self, h):
        h = str(h).lstrip("#")
        if not h or len(h) < 6:
            logger.warning(f"Invalid hex color: '{h}', falling back to red")
            return (255, 0, 0)
        try:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError as e:
            logger.error(f"Hex conversion error for '{h}': {e}")
            return (255, 0, 0)


# ============================================================
# STATE
# ============================================================
state: typing.Dict[str, typing.Any] = {
    "mode":       "static",
    "colors":     ["FF0000"] * 8,
    "speed":      50,
    "brightness": 100,
    "direction":  "ltr",
    "power":      True,
    "win_lock":   False,
}

rgb_ctrl = RGBController()
engine   = AnimationEngine(rgb_ctrl)


def save_state():
    with lock:
        try:
            snapshot = copy.deepcopy(state)
        except Exception as e:
            logger.error(f"State snapshot error: {e}")
            return
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        temp_file = f"{CONFIG_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(snapshot, f)
        os.replace(temp_file, CONFIG_FILE)
    except Exception as e:
        logger.error(f"State save error: {e}")
    finally:
        state_changed.set()


def load_state():
    with lock:
        try:
            if not os.path.exists(CONFIG_FILE):
                return
            with open(CONFIG_FILE) as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                return

            if loaded.get("mode") in VALID_LIGHT_MODES:
                state["mode"] = loaded["mode"]

            colors = loaded.get("colors")
            if isinstance(colors, list):
                cleaned: typing.List[str] = []
                for i, c in enumerate(colors):
                    if i >= 8:
                        break
                    c_str = str(c).lstrip("#").upper()
                    if HEX_COLOR_RE.match(c_str):
                        cleaned.append(c_str)
                if cleaned:
                    c0 = cleaned[0]
                    state["colors"] = (cleaned + [c0] * 8)[:8]

            speed = loaded.get("speed")
            if isinstance(speed, int):
                state["speed"] = max(1, min(speed, 100))

            brightness = loaded.get("brightness")
            if isinstance(brightness, int):
                state["brightness"] = max(0, min(brightness, 100))

            if loaded.get("direction") in VALID_DIRECTIONS:
                state["direction"] = loaded["direction"]

            if isinstance(loaded.get("power"), bool):
                state["power"] = loaded["power"]

            if isinstance(loaded.get("win_lock"), bool):
                state["win_lock"] = loaded["win_lock"]

        except Exception as e:
            logger.error(f"State load error: {e}")


# ============================================================
# D-BUS SERVICE
# ============================================================
class HPManagerService(object):
    """
    <node>
      <interface name="com.yyl.hpmanager">
        <method name="SetColor"><arg type="i" name="z" direction="in"/><arg type="s" name="h" direction="in"/><arg type="s" name="resp" direction="out"/></method>
        <method name="SetMode"><arg type="s" name="m" direction="in"/><arg type="i" name="s" direction="in"/><arg type="s" name="resp" direction="out"/></method>
        <method name="SetGlobal"><arg type="b" name="p" direction="in"/><arg type="i" name="b" direction="in"/><arg type="s" name="d" direction="in"/><arg type="s" name="resp" direction="out"/></method>
        <method name="GetState"><arg type="s" name="j" direction="out"/></method>
        <method name="SetWinLock"><arg type="b" name="locked" direction="in"/><arg type="s" name="result" direction="out"/></method>
      </interface>
    </node>
    """

    def SetColor(self, z, h):
        c = str(h).lstrip("#").upper()
        if not HEX_COLOR_RE.match(c):
            return "FAIL"
        with lock:
            state["mode"]  = "static"
            state["power"] = True
            if z == 8:
                state["colors"] = [c] * 8
            elif 0 <= z < 8:
                state["colors"][z] = c
            else:
                return "FAIL"
        save_state()
        return "OK"

    def SetMode(self, m, s):
        if m not in VALID_LIGHT_MODES:
            return "FAIL"
        with lock:
            state["mode"]  = m
            state["speed"] = max(1, min(int(s), 100))
            state["power"] = True
        save_state()
        return "OK"

    def SetGlobal(self, p, b, d):
        if d not in VALID_DIRECTIONS:
            return "FAIL"
        with lock:
            state["power"]      = bool(p)
            state["brightness"] = max(0, min(int(b), 100))
            state["direction"]  = d
        save_state()
        return "OK"

    def GetState(self):
        with lock:
            return json.dumps(state)

    def SetWinLock(self, locked):
        logger.info(f"SetWinLock: {'LOCKED' if locked else 'UNLOCKED'}")
        with lock:
            state["win_lock"] = bool(locked)
        rgb_ctrl.write_win_lock(bool(locked))
        save_state()
        return "OK"


# ============================================================
# MAIN
# ============================================================
def main():
    if os.geteuid() != 0:
        print("Root privileges required (sudo).")
        sys.exit(1)

    load_state()

    service = HPManagerService()

    if rgb_ctrl.is_available():
        rgb_ctrl.write_win_lock(state.get("win_lock", False))
        engine.start()
        logger.info("RGB engine started")
    else:
        logger.warning("RGB driver not available — lighting control disabled")

    try:
        bus = SystemBus()
        bus.publish("com.yyl.hpmanager", service)
        logger.info("HP RGB Control Daemon ready on D-Bus")
        GLib.MainLoop().run()
    except Exception as e:
        logger.critical(f"Service error: {e}")


if __name__ == "__main__":
    main()
