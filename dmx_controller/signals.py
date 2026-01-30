from __future__ import annotations

import signal
from typing import Callable


def register_signal_handlers(stop_func: Callable[[], None]) -> None:
    """Register SIGINT and SIGTERM to call stop_func.

    stop_func should be a callable that performs shutdown (e.g., Engine.stop).
    """

    def _handler(signum, frame):
        try:
            stop_func()
        except Exception:
            pass

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)
