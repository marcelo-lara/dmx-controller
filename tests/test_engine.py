import time
from types import SimpleNamespace

from dmx_controller.buffer import UniverseBuffer
from dmx_controller.controller import Controller
from dmx_controller.engine import Engine


class DummySender:
    def __init__(self):
        self.calls = []

    def send(self, data, force=False):
        self.calls.append((bytes(data), force))


def test_run_once_calls_send():
    buf = UniverseBuffer(16)
    buf.set_channel(1, 123)
    sender = DummySender()
    c = Controller(sender=sender, buffer=buf)
    engine = Engine(c)

    engine.run_once()
    assert len(sender.calls) == 1
    data, force = sender.calls[0]
    assert data[0] == 123


def test_run_loop_max_iterations(monkeypatch):
    # Monkeypatch perf_counter and sleep to make loop deterministic
    counter = {"t": 0.0}

    def fake_perf_counter():
        return counter["t"]

    slept = []

    def fake_sleep(s):
        slept.append(s)
        counter["t"] += s

    monkeypatch.setattr("time.sleep", fake_sleep)
    monkeypatch.setattr("dmx_controller.engine.perf_counter", fake_perf_counter)

    buf = UniverseBuffer(8)
    sender = DummySender()
    c = Controller(sender=sender, buffer=buf)
    engine = Engine(c, fps=10.0)

    # Run internal loop for 3 iterations
    engine._run(max_iterations=3)
    assert len(sender.calls) == 3
    # Sleep recorded should be close to interval (0.1s)
    assert all(abs(s - 0.1) < 1e-6 for s in slept)


def test_stop_calls_blackout(monkeypatch):
    buf = UniverseBuffer(8)
    sender = DummySender()
    c = Controller(sender=sender, buffer=buf)

    # ensure blackout is called from stop even without start
    engine = Engine(c)
    engine.stop()
    # final blackout should have been sent
    # the blackout sets all channels to 0 and sends force=True
    assert any(force is True for (_d, force) in sender.calls)
