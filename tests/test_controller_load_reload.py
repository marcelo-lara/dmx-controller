from pathlib import Path
from dmx_controller.controller import Controller


def test_controller_load_and_reload(tmp_path: Path):
    c = Controller()
    fp = tmp_path / "fixtures.json"
    fp.write_text('{"a":1}')
    first = c.load_fixtures(fp)
    assert first == {"a": 1}
    # change file and reload
    fp.write_text('{"a":2}')
    assert c.load_fixtures(fp, reload=True) == {"a": 2}
