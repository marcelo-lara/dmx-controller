from __future__ import annotations

import threading
import time
from time import perf_counter
from typing import Optional

from .controller import Controller


class Engine:
    """Engine that drives sending frames at a fixed FPS with graceful shutdown."""

    def __init__(self, controller: Controller, fps: float = 60.0):
        self.controller = controller
        self.fps = float(fps)
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 1.0) -> None:
        """Stop the engine and perform a final blackout (forced send)."""
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=timeout)
        # Ensure final blackout is sent
        try:
            self.controller.blackout(send=True, force=True)
        except Exception:
            # Do not raise from stop
            pass

    def _run(self, max_iterations: Optional[int] = None) -> None:
        interval = 1.0 / self.fps
        next_time = perf_counter()
        iterations = 0
        while self._running.is_set() and (max_iterations is None or iterations < max_iterations):
            now = perf_counter()
            if now < next_time:
                time.sleep(next_time - now)
            else:
                # if we're late, don't sleep
                pass

            # Send current frame
            self.controller.send_frame()

            iterations += 1
            next_time += interval

    def run_once(self) -> None:
        """Send one frame immediately (useful for deterministic testing)."""
        self.controller.send_frame()
