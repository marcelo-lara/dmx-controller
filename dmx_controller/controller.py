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
