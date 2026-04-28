# HP RGB Control

<p align="center">
  <img src="images/omenapplogo.png" alt="Logo" width="160">
</p>

A minimal fork of [OMEN Command Center for Linux](https://github.com/yunusemreyl/OmenCommandCenterforLinux) stripped down to **keyboard RGB lighting control only**. No fan control, no power profiles, no GPU MUX — just the lighting daemon and a single-page GUI.

---

## Credits

**Original project:** [OMEN Command Center for Linux](https://github.com/yunusemreyl/OmenCommandCenterforLinux)  
**Original author:** [yunusemreyl](https://github.com/yunusemreyl)  
**Original contributors:** [ja4e](https://github.com/ja4e), [babyinlinux](https://github.com/babyinlinux), [entharia](https://github.com/entharia)  
**Kernel module:** [TUXOV](https://github.com/TUXOV/hp-wmi-fan-and-backlight-control) — `hp-wmi-fan-and-backlight-control`

This fork was created by **Aaditya Bhatia** to produce a lightweight, single-purpose RGB control tool from the original full-featured application.

---

## What was changed from the original

| Component | Original | This fork |
|-----------|----------|-----------|
| Daemon | Fan, power profiles, GPU MUX, system info, keyboard fixes, RGB | **RGB only** |
| GUI | Dashboard, Fan page, MUX page, Keyboard page, Settings page, Lighting page | **Lighting page only** |
| Dependencies | GTK4, pydbus, cairo, power-profiles-daemon (optional) | GTK4, pydbus, cairo |
| Driver | Unchanged | **Unchanged** (hp-wmi + hp-rgb-lighting) |
| Lighting modes | Static, Breathing, Wave, Cycle | Static, Breathing, Wave, Cycle, **Pulse, Chase, Comet, Twinkle** |

The kernel driver (`driver/`) is **not modified** — it is the same driver from the original project.

---

## Lighting Modes

| Mode | Description |
|------|-------------|
| **Static** | All zones a fixed color |
| **Breathing** | All zones fade in and out together |
| **Wave** | Your chosen colors scroll across zones |
| **Cycle** | All zones cycle through the full color wheel |
| **Pulse** | Each zone breathes with a 90° phase offset — a rolling wave of light |
| **Chase** | A single bright zone (with fading trail) bounces left ↔ right |
| **Comet** | A bright head with a dimming tail loops continuously around all zones |
| **Twinkle** | Each zone independently flashes a random color at random intervals |

Speed and brightness controls apply to all animated modes. The direction toggle (→ / ←) applies to Wave, Pulse, Chase, and Comet.

---

## Installation

```bash
git clone <this-repo-url>
cd OmenCommandCenterforLinux
chmod +x setup.sh
sudo ./setup.sh install
```

### Quick reinstall (after editing source files)

```bash
sudo ./reinstall.sh
```

This stops the daemon, copies updated files in place, and restarts — no driver rebuild needed.

### Uninstall

```bash
sudo ./setup.sh uninstall
```

---

## Requirements

- Linux (Ubuntu 22.04+, Fedora 38+, Arch, OpenSUSE Tumbleweed)
- Python 3.10+
- GTK 4.0
- `python3-pydbus` / `python-pydbus`
- `libadwaita` (optional but recommended for theming)
- HP OMEN or Victus laptop with the `hp-rgb-lighting` kernel module loaded

---

## Compatibility

Inherits the hardware compatibility of the original project. The RGB driver supports HP OMEN and Victus series laptops running kernel ≥ 5.15.

---

## License

Same as the original project (open source). See the original repository for license details.
