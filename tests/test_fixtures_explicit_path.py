from pathlib import Path
from dmx_controller.fixtures import parse_fixtures_json


def test_explicit_path_overrides(tmp_path: Path):
    fp = tmp_path / "fixtures.json"
    obj = {"override": True}
    fp.write_text(__import__("json").dumps(obj))
    assert parse_fixtures_json(fp) == obj
