# DMX Controller

A small, dependency-free Python library to build and emit Art-Net DMX frames.
The package contains a thread-safe universe buffer, an Art-Net packet sender, a simple 60FPS engine, and fixture helpers.

## Quick start

Install dev tools (for running tests locally):

```bash
python3.10 -m venv dmx-controller
source dmx-controller/bin/activate
pip install -r requirements.txt
```

Run the example (dry run):

```bash
python examples/simple_run.py --dry-run
```

Run tests:

```bash
pytest -q
```

## Core concepts

- Universe buffer (512 channels): thread-safe `UniverseBuffer` with a 1-based public API.
- Sender: `ArtNetSender` builds ArtDMX packets and sends them via UDP. Supports socket reuse, retries, timeout, and a sequence counter.
- Controller: `Controller` ties the buffer and sender and exposes `send_frame()` and `blackout()`.
- Engine: `Engine` runs a timing loop to send frames at a target FPS and performs a forced blackout on `stop()`.
- Fixtures: packaged fixtures (JSON) and helpers to load and map fixture logical values to DMX channels.

## Fixtures

The repository includes a default `fixtures.json` at `dmx_controller/data/fixtures.json`.
You can load fixtures from:

1. An explicit path: `Controller.load_fixtures(path='path/to/fixtures.json')` or `parse_fixtures_json(path)`.
2. Packaged data (default): `parse_fixtures_json()`.
3. Fallback: `./fixtures.json` in current working directory.

`Controller.load_fixtures(path=None, reload=False)` caches parsed fixtures; pass `reload=True` to force re-read.

## Development & testing

- Python 3.10+ is required (typing uses 3.10 features).
- Tests use `pytest`; dev tools are listed in `requirements.txt`.
- CI: GitHub Actions workflow runs tests on Python 3.10.

## Packaging

- Package metadata is in `pyproject.toml` and `setup.cfg`.
- `dmx_controller/data/fixtures.json` is included as package data via `MANIFEST.in` and `setup.cfg`.

## Contact

See repository files and tests for examples and API usage. Open an issue or PR with questions or improvements.
