from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Iterable

from .utils import msb_lsb


_COLOR_PRESETS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
}


@dataclass
class Fixture:
    id: str
    name: str
    type: str
    channels: Dict[str, int]
    current_values: Dict[str, Any] = field(default_factory=dict)
    buffer: Optional[object] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    arm_values: Dict[str, int] = field(default_factory=dict)
    controller: Optional[object] = None

    def _apply_channel_updates(self, updates: Iterable[tuple[int, int]]) -> None:
        """Write channel updates to the bound buffer if present and notify the
        controller that this fixture was just configured (so sends can be limited
        to this fixture if desired).
        """
        if self.buffer is None:
            # not bound, keep values locally
            for ch, val in updates:
                # update current values by channel index is not tracked here
                pass
            # still notify controller even when buffer isn't present
            if self.controller is not None:
                try:
                    self.controller._mark_configured(self)
                except Exception:
                    pass
            return
        # buffer exposes set_channels
        self.buffer.set_channels(updates)
        if self.controller is not None:
            try:
                self.controller._mark_configured(self)
            except Exception:
                pass
    def set_value(self, logical: str, value: int) -> Dict[int, int]:
        """Map a logical value to channel updates (returns mapping channel->value)."""
        if logical not in self.channels:
            raise KeyError(f"Unknown logical channel {logical}")
        ch = self.channels[logical]
        self.current_values[logical] = value
        updates = {ch: int(value)}
        self._apply_channel_updates(updates.items())
        return updates

    # high-level convenience properties for example script
    @property
    def dimmer(self) -> float:
        val = self.current_values.get("dim") or self.current_values.get("dimmer") or 0
        # normalize to 0..1
        try:
            return float(val) / 255.0
        except Exception:
            return 0.0

    @dimmer.setter
    def dimmer(self, value: float) -> None:
        # Accept 0..1 floats or 0..255 ints
        if isinstance(value, float) or isinstance(value, int):
            if 0.0 <= float(value) <= 1.0:
                v = int(round(float(value) * 255.0))
            else:
                v = int(value)
        else:
            raise TypeError("dimmer must be float 0.0..1.0 or int 0..255")
        # find candidate channel(s)
        target = None
        # check meta channel types first
        for logical, typ in (self.meta.get("channel_types") or {}).items():
            if typ in ("dimmer", "dimmer"):
                target = self.channels.get(logical)
                break
        # fallback to common names
        if target is None:
            for candidate in ("dim", "dimmer", "intensity", "level"):
                if candidate in self.channels:
                    target = self.channels[candidate]
                    break
        if target is None:
            raise KeyError("No dimmer channel present for fixture")
        self.current_values["dim"] = v
        self._apply_channel_updates(((target, v),))

    @property
    def color(self):
        return self.current_values.get("color")

    @color.setter
    def color(self, value) -> None:
        # RGB fixtures
        if "red" in self.channels and "green" in self.channels and "blue" in self.channels:
            if isinstance(value, str):
                rgb = _COLOR_PRESETS.get(value.lower())
                if rgb is None:
                    raise ValueError(f"Unknown color preset: {value}")
            elif isinstance(value, (list, tuple)) and len(value) == 3:
                rgb = tuple(int(max(0, min(255, int(x)))) for x in value)
            else:
                raise TypeError("color must be a preset name or (r,g,b) tuple")
            updates = []
            updates.append((self.channels["red"], rgb[0]))
            updates.append((self.channels["green"], rgb[1]))
            updates.append((self.channels["blue"], rgb[2]))
            self.current_values.update({"red": rgb[0], "green": rgb[1], "blue": rgb[2]})
            self._apply_channel_updates(updates)
            return

        # single wheel / numeric-mapped color (moving heads)
        if "color" in self.channels:
            # try to map by name using meta.value_mappings
            vm = self.meta.get("value_mappings", {}).get("color") if self.meta else None
            if isinstance(value, str) and vm:
                # find key whose mapped value matches (case-insensitive)
                for k, name in vm.items():
                    if str(name).lower() == value.lower():
                        v = int(k)
                        self.current_values["color"] = v
                        self._apply_channel_updates(((self.channels["color"], v),))
                        return
            # otherwise if value numeric
            if isinstance(value, int):
                v = int(max(0, min(255, value)))
                self.current_values["color"] = v
                self._apply_channel_updates(((self.channels["color"], v),))
                return
            raise TypeError("Unsupported color value for fixture")

    def arm(self) -> None:
        """Apply the configured arm values for this fixture (if any)."""
        if not self.arm_values:
            # try to read arm from meta or stored attribute
            pass
        updates = []
        for k, v in (self.arm_values or {}).items():
            if k in self.channels:
                updates.append((self.channels[k], int(v)))
        if updates:
            self._apply_channel_updates(updates)


class ParCanFixture(Fixture):
    def set_color_rgb(self, r: int, g: int, b: int) -> Dict[int, int]:
        updates = {}
        if "red" in self.channels:
            updates[self.channels["red"]] = r
        if "green" in self.channels:
            updates[self.channels["green"]] = g
        if "blue" in self.channels:
            updates[self.channels["blue"]] = b
        self.current_values.update({"red": r, "green": g, "blue": b})
        self._apply_channel_updates(tuple(updates.items()))
        return updates


class MovingHeadFixture(Fixture):
    def set_pan_tilt(self, pan: int, tilt: int) -> Dict[int, int]:
        updates = {}
        if "pan_msb" in self.channels and "pan_lsb" in self.channels:
            msb, lsb = msb_lsb(pan)
            updates[self.channels["pan_msb"]] = msb
            updates[self.channels["pan_lsb"]] = lsb
            self.current_values["pan"] = pan
        if "tilt_msb" in self.channels and "tilt_lsb" in self.channels:
            msb, lsb = msb_lsb(tilt)
            updates[self.channels["tilt_msb"]] = msb
            updates[self.channels["tilt_lsb"]] = lsb
            self.current_values["tilt"] = tilt
        self._apply_channel_updates(tuple(updates.items()))
        return updates
