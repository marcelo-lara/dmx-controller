from __future__ import annotations

from pathlib import Path
from typing import Optional
import threading
import time

from .fixtures import parse_fixtures_json
from .buffer import UniverseBuffer
from .artnet import ArtNetSender, DEFAULT_FPS, ARTNET_PORT
from .fixture_types import Fixture, ParCanFixture, MovingHeadFixture


class Controller:
    """High-level controller managing fixtures, the universe buffer and sender.

    New behavior (no backward compatibility):
      - Controller() will create a default UniverseBuffer and ArtNetSender when not
        provided. You can override network settings via constructor parameters.
      - `start()` spawns a background thread that sends the current buffer at the
        configured FPS until `stop()` is called.
      - `fixtures` property returns a list of Fixture objects that are bound to
        this controller's buffer (setting fixture properties writes to the buffer).
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = ARTNET_PORT,
        universe: int = 0,
        fps: int = DEFAULT_FPS,
        sender: Optional[ArtNetSender] = None,
        buffer: Optional[UniverseBuffer] = None,
        fixtures_path: Optional[Path | str] = None,
        debug: bool = False,
    ):
        self._host = host
        self._port = port
        self._universe = universe
        self._fps = fps
        # debug mode: when True, the ArtNetSender will dump the DMX payload as
        # space-separated uppercase hex bytes ("FF FF 00 ...") each time a
        # frame is actually sent to the node.
        self.debug = bool(debug)
        if sender is not None:
            self.sender = sender
            # if a sender instance is provided, set its debug flag too
            try:
                setattr(self.sender, "debug", self.debug)
            except Exception:
                pass
        else:
            self.sender = ArtNetSender(host=host, port=port, universe=universe, fps=fps, debug=self.debug)

        self.buffer = buffer if buffer is not None else UniverseBuffer()

        # fixtures will be a dict id->Fixture instances
        self._fixtures: dict | None = None
        self._fixtures_source: Path | None = Path(fixtures_path) if fixtures_path is not None else None

        # runtime control for the sender thread
        self._tx_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def load_fixtures(self, path: Optional[Path | str] = None, reload: bool = False) -> dict:
        """Load fixtures from JSON and convert them to Fixture objects bound to
        this controller's buffer.

        Returns a dict mapping fixture id -> Fixture instance.
        """
        if path is None and self._fixtures is not None and not reload:
            return self._fixtures

        fixtures_data = parse_fixtures_json(path)
        # Support two possible fixture formats:
        # - legacy / arbitrary JSON maps (e.g. tests expect load_fixtures to return a dict)
        # - the packaged fixtures list of fixture definitions (normal runtime case)
        if isinstance(fixtures_data, dict):
            # preserve legacy behavior: return the parsed dict directly
            self._fixtures = fixtures_data
            self._fixtures_source = Path(path) if path is not None else self._fixtures_source
            return fixtures_data

        fixtures = {}
        for item in fixtures_data:
            ftype = item.get("type", "")
            if "moving" in ftype:
                cls = MovingHeadFixture
            elif "rgb" in ftype or "par" in ftype:
                cls = ParCanFixture
            else:
                cls = Fixture
            inst = cls(
                id=item.get("id"),
                name=item.get("name"),
                type=item.get("type"),
                channels=item.get("channels", {}),
                current_values=item.get("current_values", {}),
                buffer=self.buffer,
                meta=item.get("meta", {}),
                arm_values=item.get("arm", {}),
                controller=self,
            )
            fixtures[inst.id] = inst

        self._fixtures = fixtures
        self._fixtures_source = Path(path) if path is not None else self._fixtures_source
        return fixtures

    def arm_fixtures(self, send: bool = True, force: bool = True) -> None:
        """Apply configured arm values for all fixtures and optionally send a frame.

        - `send`: if True, call `send_frame()` after applying arm values.
        - `force`: if True, bypass sender rate limiting when sending.
        """
        # ensure fixtures are loaded
        _ = self.fixtures
        for f in self._fixtures.values():
            try:
                f.arm()
            except Exception:
                # tolerate individual fixture failures
                pass
        if send:
            self.send_frame(force=force)

    @property
    def fixtures(self) -> list[Fixture]:
        """Return fixtures as a list. If not loaded, lazy-load package data."""
        if self._fixtures is None:
            self.load_fixtures(self._fixtures_source)
        return list(self._fixtures.values())

    def _mark_configured(self, fixture: Fixture) -> None:
        """Internal: mark the given fixture as the most recently configured."""
        try:
            self._last_configured_fixture = fixture
        except Exception:
            self._last_configured_fixture = None

    def send_frame(self, force: bool = False) -> None:
        """Snapshot the buffer and send via the configured sender.

        If no buffer or sender is configured, this is a no-op. If a fixture has
        been recently configured, the payload will be trimmed to the highest
        channel index present in that fixture's channel map.
        """
        if self.buffer is None or self.sender is None:
            return
        data = self.buffer.snapshot()

        # If we have a last-configured fixture, limit the payload to its
        # highest channel index so we only send necessary channels.
        if getattr(self, "_last_configured_fixture", None) is not None:
            try:
                chans = list(self._last_configured_fixture.channels.values())
                if chans:
                    max_ch = max(chans)
                    # snapshot is bytes (0-based) and channels are 1-based
                    send_data = data[:max_ch]
                else:
                    send_data = data
            except Exception:
                send_data = data
        else:
            send_data = data

        sent = self.sender.send(data, force=force)

        # If the send actually happened and debug mode is enabled, print a
        # trimmed hex dump limited to the last-configured fixture's highest
        # channel. This ensures we always send the full universe but only log
        # the relevant portion.
        if sent and getattr(self, "debug", False):
            try:
                if getattr(self, "_last_configured_fixture", None) is not None:
                    chans = list(self._last_configured_fixture.channels.values())
                    if chans:
                        max_ch = max(chans)
                        dump = data[:max_ch]
                    else:
                        dump = data
                else:
                    dump = data
                print(" ".join(f"{b:02X}" for b in dump))
            except Exception:
                pass

    def _sender_loop(self) -> None:
        """Background loop that sends frames at the configured FPS until stopped."""
        interval = 1.0 / float(self._fps) if self._fps > 0 else 1.0 / DEFAULT_FPS
        while not self._stop_event.is_set():
            try:
                self.send_frame(force=False)
            except Exception:
                # don't let the thread die on transient errors
                pass
            # wait with small granularity so stop() becomes responsive
            waited = 0.0
            step = min(0.01, interval)
            while waited < interval and not self._stop_event.is_set():
                time.sleep(step)
                waited += step

    def start(self) -> None:
        """Start the background sender thread. Idempotent."""
        if self._tx_thread is not None and self._tx_thread.is_alive():
            return
        self._stop_event.clear()
        self._tx_thread = threading.Thread(target=self._sender_loop, name="dmx-sender", daemon=True)
        self._tx_thread.start()

    def stop(self) -> None:
        """Stop the background sender thread and close the sender socket."""
        self._stop_event.set()
        if self._tx_thread is not None:
            self._tx_thread.join(timeout=1.0)
            self._tx_thread = None
        try:
            if self.sender is not None:
                self.sender.close()
        except Exception:
            pass

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
