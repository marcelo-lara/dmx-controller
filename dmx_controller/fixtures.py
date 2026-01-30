from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Optional


def parse_fixtures_json(path: Optional[Path | str] = None) -> dict:
    """Load and parse fixtures JSON.

    Loading order:
      1. Explicit `path` if provided.
      2. Packaged data: `dmx_controller/data/fixtures.json` via importlib.resources.
      3. Fallback to `Path.cwd()/fixtures.json`.

    Raises FileNotFoundError if no file found.
    """
    # Explicit path
    if path is not None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Fixtures file not found at {p}")
        return json.loads(p.read_text())

    # Packaged data
    try:
        pkg_file = resources.files("dmx_controller").joinpath("data/fixtures.json")
        with resources.as_file(pkg_file) as p:
            return json.loads(p.read_text())
    except Exception:
        # Fall back to cwd
        fallback = Path.cwd() / "fixtures.json"
        if fallback.exists():
            return json.loads(fallback.read_text())
        raise FileNotFoundError("No fixtures.json found (explicit path, package data, or cwd)")
