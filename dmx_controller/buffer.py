from __future__ import annotations

import threading
from typing import Iterable


class UniverseBuffer:
    """Thread-safe universe buffer with 1-based public API."""

    def __init__(self, channels: int = 512):
        self._channels = channels
        self._buf = bytearray(channels)
        self._lock = threading.Lock()

    def set_channel(self, channel: int, value: int) -> None:
        """Set channel value. Public API is 1-based channel numbering."""
        if not 1 <= channel <= self._channels:
            raise IndexError("channel out of range (1-based)")
        if not 0 <= value <= 255:
            raise ValueError("value must be 0..255")
        with self._lock:
            self._buf[channel - 1] = value

    def get_channel(self, channel: int) -> int:
        if not 1 <= channel <= self._channels:
            raise IndexError("channel out of range (1-based)")
        with self._lock:
            return self._buf[channel - 1]

    def snapshot(self) -> bytes:
        """Return an immutable copy of the universe state."""
        with self._lock:
            return bytes(self._buf)

    def set_channels(self, updates: Iterable[tuple[int, int]]) -> None:
        """Atomically apply multiple (channel, value) updates."""
        with self._lock:
            for ch, val in updates:
                if not 1 <= ch <= self._channels:
                    raise IndexError("channel out of range (1-based)")
                if not 0 <= val <= 255:
                    raise ValueError("value must be 0..255")
                self._buf[ch - 1] = val
