from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

from .utils import msb_lsb


@dataclass
class Fixture:
    id: str
    name: str
    type: str
    channels: Dict[str, int]
    current_values: Dict[str, Any] = field(default_factory=dict)

    def set_value(self, logical: str, value: int) -> Dict[int, int]:
        """Map a logical value to channel updates (returns mapping channel->value)."""
        if logical not in self.channels:
            raise KeyError(f"Unknown logical channel {logical}")
        ch = self.channels[logical]
        self.current_values[logical] = value
        return {ch: int(value)}


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
        return updates
