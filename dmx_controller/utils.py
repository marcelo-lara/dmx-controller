from __future__ import annotations


def msb_lsb(value: int) -> tuple[int, int]:
    """Return (MSB, LSB) for 16-bit value (0..65535)."""
    if not 0 <= value <= 0xFFFF:
        raise ValueError("value must be 0..65535")
    msb = (value >> 8) & 0xFF
    lsb = value & 0xFF
    return msb, lsb
