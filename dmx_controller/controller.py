from __future__ import annotations

from pathlib import Path
from typing import Optional

from .fixtures import parse_fixtures_json


class Controller:
    """High-level controller managing fixtures and the universe buffer."""

    def __init__(self, sender=None, buffer=None):
        self.sender = sender
        self.buffer = buffer
        self._fixtures: dict | None = None
        self._fixtures_source: Path | None = None

    def load_fixtures(self, path: Optional[Path | str] = None, reload: bool = False) -> dict:
        """Load and cache fixtures.

        - If `path` provided: load from path and update cache.
        - If no `path` and cache exists and `reload` is False: return cached fixtures.
        - Otherwise use `parse_fixtures_json(None)` which loads package data or cwd fallback.
        """
        if path is None and self._fixtures is not None and not reload:
            return self._fixtures

        fixtures = parse_fixtures_json(path)
        self._fixtures = fixtures
        self._fixtures_source = Path(path) if path is not None else None
        return fixtures

    def send_frame(self, force: bool = False) -> None:
        """Snapshot the buffer and send via the configured sender.

        If no buffer or sender is configured, this is a no-op.
        """
        if self.buffer is None or self.sender is None:
            return
        data = self.buffer.snapshot()
        self.sender.send(data, force=force)

    def blackout(self, send: bool = True, force: bool = True) -> None:
        """Set all channels to zero and optionally send immediately.

        - `send`: if True, calls send_frame(force=force)
        - `force`: if True, bypasses the sender rate limiter
        """
        if self.buffer is None:
            return
        # Zero all channels (use buffer API to avoid size assumptions)
        self.buffer.zero_all()
        if send:
            self.send_frame(force=force)
