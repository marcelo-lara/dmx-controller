from dmx_controller.signals import register_signal_handlers


class Fake:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


def test_register_signal_handlers_calls_stop(monkeypatch):
    f = Fake()

    # Register handlers
    register_signal_handlers(f.stop)

    # Simulate calling the handler directly
    import signal

    handler = signal.getsignal(signal.SIGINT)
    # Call the handler
    handler(signal.SIGINT, None)
    assert f.stopped is True
