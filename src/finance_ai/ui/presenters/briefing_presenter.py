import tkinter
from enum import Enum
from typing import NamedTuple

from finance_ai.ai.advisor import StrategicAdvisor
from finance_ai.ai.background import BackgroundTask
from finance_ai.ai.errors import describe_ai_error
from finance_ai.ai.thinking import (
    EXECUTIVE_BRIEFING_THINKING_STEPS,
    ThinkingAnimator,
    ThinkingState,
)


class BriefingRequestState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class BriefingListener(NamedTuple):
    on_thinking_update: object
    on_success: object
    on_error: object


class BriefingPresenter:
    """Owns the Executive Briefing request's lifecycle independent of any one view.

    A BriefingView is destroyed and recreated every time the desktop sidebar navigates
    away and back (MainWindow rebuilds the whole content frame per page). If the request
    itself lived on the view, navigating away mid-request would strand the result nowhere
    to land once it completed. This presenter is owned by MainWindow instead, so it
    outlives any single view: attach()/detach() let a (re)created view subscribe to
    whatever is currently happening, and generate() schedules its timers on a permanent
    widget (the root window) rather than the page-scoped view.
    """

    def __init__(self, month: str = "2026-06"):
        self.month = month
        self.advisor = StrategicAdvisor()
        self.animator = ThinkingAnimator(
            EXECUTIVE_BRIEFING_THINKING_STEPS,
            on_update=self._handle_thinking_update,
        )
        self._task: BackgroundTask | None = None
        self._listener: BriefingListener | None = None

        self.state = BriefingRequestState.IDLE
        self.thinking_state: ThinkingState | None = None
        self.result_text: str | None = None

    def attach(self, on_thinking_update, on_success, on_error) -> None:
        self._listener = BriefingListener(on_thinking_update, on_success, on_error)

        if self.state == BriefingRequestState.RUNNING and self.thinking_state:
            on_thinking_update(self.thinking_state)
        elif self.state == BriefingRequestState.DONE and self.result_text is not None:
            on_success(self.result_text)
        elif self.state == BriefingRequestState.ERROR and self.result_text is not None:
            on_error(self.result_text)

    def detach(self) -> None:
        self._listener = None

    def generate(self, widget) -> None:
        if self.state == BriefingRequestState.RUNNING:
            return

        self.state = BriefingRequestState.RUNNING
        self.thinking_state = None
        self.animator.start(widget)

        self._task = BackgroundTask(
            target=lambda: self.advisor.executive_briefing(self.month),
            on_success=self._handle_success,
            on_error=self._handle_error,
        )
        self._task.start()
        self._task.poll(widget)

    def _handle_thinking_update(self, state: ThinkingState) -> None:
        self.thinking_state = state
        self._notify(lambda listener: listener.on_thinking_update(state))

    def _handle_success(self, text: str) -> None:
        self.animator.stop()
        self.state = BriefingRequestState.DONE
        self.result_text = text
        self._notify(lambda listener: listener.on_success(text))

    def _handle_error(self, exc: Exception) -> None:
        self.animator.stop()
        self.state = BriefingRequestState.ERROR
        self.result_text = describe_ai_error(exc)
        self._notify(lambda listener: listener.on_error(self.result_text))

    def _notify(self, call) -> None:
        if not self._listener:
            return

        try:
            call(self._listener)
        except tkinter.TclError:
            # The attached view's widgets were torn down (e.g. the user navigated away)
            # without detach() running first -- <Destroy> and an already-scheduled
            # animator/poll callback aren't strictly ordered, so this can race. Treat a
            # dead widget as an implicit detach instead of crashing the callback.
            self._listener = None
