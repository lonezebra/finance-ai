from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ThinkingPhase(str, Enum):
    BUILD_CONTEXT = "Building financial context..."
    REVIEW_CHANGES = "Reviewing changes since your last update..."
    ANALYZE_DECISIONS = "Evaluating decision tradeoffs..."
    GENERATE_RESPONSE = "Generating strategic recommendation..."


@dataclass(frozen=True)
class ThinkingState:
    phase: ThinkingPhase
    progress: int


# Mirrors the actual create_executive_report() -> format_executive_report_for_ai() ->
# AIRuntime.ask() pipeline. There is no separate health/confidence-score review step in that
# pipeline (that belongs to the older, unrelated Opportunity Engine), so these phases don't
# claim one.
EXECUTIVE_BRIEFING_THINKING_STEPS = [
    ThinkingState(ThinkingPhase.BUILD_CONTEXT, 15),
    ThinkingState(ThinkingPhase.REVIEW_CHANGES, 40),
    ThinkingState(ThinkingPhase.ANALYZE_DECISIONS, 65),
    ThinkingState(ThinkingPhase.GENERATE_RESPONSE, 90),
]


class ThinkingAnimator:
    """Cycles through a fixed list of ThinkingStates on a timer.

    The AI call this narrates is a single blocking request with no visibility into its
    internal progress, so this is cosmetic pacing, not a measurement of real work done.
    It advances once through the steps and then holds on the last one until stop() is
    called, rather than looping, so it doesn't imply progress beyond what it can promise.
    """

    def __init__(
        self,
        steps: list[ThinkingState],
        on_update: Callable[[ThinkingState], None],
        step_duration_ms: int = 2500,
    ):
        self._steps = steps
        self._on_update = on_update
        self._step_duration_ms = step_duration_ms
        self._index = 0
        self._stopped = False

    def start(self, widget) -> None:
        self._stopped = False
        self._index = 0
        self._tick(widget)

    def stop(self) -> None:
        self._stopped = True

    def _tick(self, widget) -> None:
        if self._stopped or self._index >= len(self._steps):
            return

        self._on_update(self._steps[self._index])
        self._index += 1

        if self._index < len(self._steps):
            widget.after(self._step_duration_ms, lambda: self._tick(widget))
