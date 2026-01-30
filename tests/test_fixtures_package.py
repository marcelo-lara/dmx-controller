import json
from importlib import resources

from dmx_controller.fixtures import parse_fixtures_json


def test_package_fixtures_loadable():
    pkg_file = resources.files("dmx_controller").joinpath("data/fixtures.json")
    with resources.as_file(pkg_file) as p:
        expected = json.loads(p.read_text())
    assert parse_fixtures_json(None) == expected
