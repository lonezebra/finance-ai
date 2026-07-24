import queue
import threading
from collections.abc import Callable
from typing import Any


class BackgroundTask:
    """Runs a blocking call off the Tkinter main thread and delivers the result back to it.

    CustomTkinter (like all Tkinter) isn't thread-safe for widget updates from a worker
    thread, so the result crosses back via a queue that poll() drains from the main thread,
    scheduled through widget.after() rather than a callback fired directly from the worker.
    """

    def __init__(
        self,
        target: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ):
        self._target = target
        self._on_success = on_success
        self._on_error = on_error
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def join(self, timeout: float | None = None) -> None:
        self._thread.join(timeout)

    def _run(self) -> None:
        try:
            result = self._target()
        except Exception as exc:  # noqa: BLE001 - forwarded to on_error, not swallowed
            self._queue.put(("error", exc))
        else:
            self._queue.put(("success", result))

    def poll(self, widget, interval_ms: int = 100) -> None:
        try:
            status, payload = self._queue.get_nowait()
        except queue.Empty:
            widget.after(interval_ms, lambda: self.poll(widget, interval_ms))
            return

        if status == "success":
            self._on_success(payload)
        else:
            self._on_error(payload)
