import tkinter
from enum import Enum

from finance_ai.ai.advisor import StrategicAdvisor
from finance_ai.ai.background import BackgroundTask
from finance_ai.ai.errors import describe_ai_error
from finance_ai.finance.metrics import default_report_month
from finance_ai.scenario.engine import run_scenario as _run_scenario
from finance_ai.scenario.models import AdjustmentType, Scenario, ScenarioAdjustment, ScenarioResult


class NarrativeState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class ScenarioPresenter:
    """Owns the scenario builder's lifecycle independent of any one view, same reasoning as
    BriefingPresenter/ChatPresenter: ScenarioView is destroyed and recreated on every sidebar
    navigation, so the adjustments being built, the last deterministic result, and any
    in-flight AI explanation need to live somewhere that survives that -- MainWindow, not the
    view.

    run_scenario_fn and advisor are injectable so this can be tested without a real database
    or LM Studio, the same pattern used for import_dataset()'s session_factory.
    """

    def __init__(
        self,
        month: str | None = None,
        run_scenario_fn=_run_scenario,
        advisor: StrategicAdvisor | None = None,
        default_month_fn=default_report_month,
    ):
        # None means "whatever month the data is about", resolved via default_month_fn on
        # every Run Scenario -- not once at construction, since this presenter is built at
        # app start and the user may import data afterwards. Resolved here rather than
        # left to run_scenario()'s own None-handling because the month is also part of the
        # scenario's name, which is built before the engine runs.
        self.month = month
        self._run_scenario_fn = run_scenario_fn
        self._default_month_fn = default_month_fn
        self.advisor = advisor or StrategicAdvisor()

        self.adjustments: list[ScenarioAdjustment] = []
        self.result: ScenarioResult | None = None

        self.narrative_state = NarrativeState.IDLE
        self.narrative_text: str | None = None

        self._task: BackgroundTask | None = None
        self._on_change = None

    def attach(self, on_change) -> None:
        self._on_change = on_change
        on_change()

    def detach(self) -> None:
        self._on_change = None

    def add_adjustment(self, adjustment_type: AdjustmentType, amount: float, label: str) -> None:
        self.adjustments.append(
            ScenarioAdjustment(type=adjustment_type, amount=amount, label=label)
        )
        self._notify()

    def remove_adjustment(self, index: int) -> None:
        del self.adjustments[index]
        self._notify()

    def run_scenario(self) -> None:
        if not self.adjustments:
            return

        month = self.month or self._default_month_fn()
        scenario = Scenario(name=f"Scenario for {month}", adjustments=list(self.adjustments))
        self.result = self._run_scenario_fn(month, scenario)
        self.narrative_state = NarrativeState.IDLE
        self.narrative_text = None
        self._notify()

    def explain_with_ai(self, widget) -> None:
        if self.result is None or self.narrative_state == NarrativeState.RUNNING:
            return

        self.narrative_state = NarrativeState.RUNNING
        self._notify()

        scenario = self.result.scenario
        # The month the result was actually computed for, not a re-resolved one -- if an
        # import lands between Run Scenario and Explain, the explanation should describe
        # the projection on screen, not a different month's baseline.
        month = self.result.baseline_snapshot.month
        self._task = BackgroundTask(
            target=lambda: self.advisor.explain_scenario(month, scenario),
            on_success=self._handle_success,
            on_error=self._handle_error,
        )
        self._task.start()
        self._task.poll(widget)

    def _handle_success(self, text: str) -> None:
        self.narrative_state = NarrativeState.DONE
        self.narrative_text = text
        self._notify()

    def _handle_error(self, exc: Exception) -> None:
        self.narrative_state = NarrativeState.ERROR
        self.narrative_text = describe_ai_error(exc)
        self._notify()

    def _notify(self) -> None:
        if not self._on_change:
            return

        try:
            self._on_change()
        except tkinter.TclError:
            # Same race as BriefingPresenter/ChatPresenter: <Destroy> and an already-scheduled
            # callback aren't strictly ordered, so this can fire against a torn-down widget.
            self._on_change = None
