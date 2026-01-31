# DMX Controller

A small, dependency-free Python library to build and emit Art-Net DMX frames.
The package contains a thread-safe universe buffer, an Art-Net packet sender, a timing engine, and fixture helpers.

## Quick start

Install dev tools (for running tests locally):

```bash
python3.10 -m venv dmx-controller
source dmx-controller/bin/activate
pip install -r requirements.txt
```

Run the example (uses `example.py` in the repo root):

```bash
python example.py
```

Run tests:

```bash
pytest -q
```

---

## Example (usage)

This project exposes a simple, high-level `Controller` API inspired by the `example.py` script.
The controller creates an internal `UniverseBuffer` and `ArtNetSender` by default; buffer and sender management are intentionally internal details.

```python
import dmx_controller
import time

c = dmx_controller.Controller(host="192.168.10.221", debug=False)

# start background sender loop (sends at the configured FPS)
c.start()

# access fixtures (loaded from packaged fixtures by default)
for f in c.fixtures:
    print(f"{f.name} ({f.id})")

    # arm the fixture (applies configured 'arm' values)
    f.arm()

    # set intensity (0.0..1.0 floats are accepted)
    f.dimmer = 1.0

    # set color (preset name or (r,g,b) tuple)
    f.color = "blue"

    time.sleep(0.5)

# wait and then blackout all channels
time.sleep(2)
c.blackout()

# stop sender and clean up
c.stop()
```

### Notes
- `Controller(...)` accepts: `host`, `port`, `universe`, `fps`, and `debug` (when `debug=True` a space-separated uppercase hex dump of the DMX payload is printed each time a frame is actually sent; the dump is limited to the most recently configured fixture for readability).
- `fixtures` is a read-only property returning a list of fixture objects bound to this controller's internal buffer. Modifying a fixture (e.g., setting `dimmer`) writes to the controller's buffer.
- The full DMX universe (512 channels) is always sent to the Art-Net node; debug output is only a trimmed view for convenience.
- Prefer the high-level `Controller` and fixture helpers; direct use of `UniverseBuffer` and low-level sender methods is considered internal and may change.

---

## Core concepts

- Universe buffer (512 channels): thread-safe `UniverseBuffer` with a 1-based public API. Intended to be used internally by `Controller` and fixture helpers.
- Sender: `ArtNetSender` builds ArtDMX packets and sends them via UDP. It supports socket reuse, retries, timeout, and a sequence counter.
- Controller: high-level glue that manages fixtures, the universe, and the sender. Use `start()`/`stop()`, `blackout()`, or `send_frame()` for manual sends.
- Fixtures: packaged fixtures (`dmx_controller/data/fixtures.json`) describe fixture channel maps and 'arm' values; helpers convert logical values (e.g., `pan`, `tilt`, `red`) into DMX channel writes.

## Development & testing

- Python 3.10+ is required.
- Tests use `pytest`; dev tools are listed in `requirements.txt`.

## Contact

See `example.py` and the `tests/` directory for usage examples and expected behavior. Open an issue or PR with questions or improvements.
