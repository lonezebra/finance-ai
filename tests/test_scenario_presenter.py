import tkinter
from datetime import datetime

from finance_ai.decision.models import DecisionSet
from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.history.models import SnapshotComparison, SnapshotRecord
from finance_ai.scenario.models import AdjustmentType, Scenario, ScenarioResult
from finance_ai.ui.presenters.scenario_presenter import NarrativeState, ScenarioPresenter


class _FakeWidget:
    def after(self, ms, callback):
        pass


def make_snapshot() -> FinancialSnapshot:
    return FinancialSnapshot(
        month="2026-06",
        total_assets=600000,
        total_debt=25000,
        net_worth=575000,
        cash_balance=50000,
        monthly_income=7000,
        monthly_expenses=3000,
        monthly_cash_flow=4000,
        savings_rate=4000 / 7000,
        debt_to_income_ratio=500 / 7000,
        emergency_fund_months=50000 / 3000,
    )


def make_scenario_result(scenario: Scenario) -> ScenarioResult:
    snapshot = make_snapshot()
    record = SnapshotRecord(id=None, created_at=datetime.now(), snapshot=snapshot)
    comparison = SnapshotComparison(previous=record, current=record, differences=[])

    return ScenarioResult(
        scenario=scenario,
        baseline_snapshot=snapshot,
        projected_snapshot=snapshot,
        comparison=comparison,
        projected_decisions=DecisionSet(decisions=[]),
        scenario_facts=["Raise: monthly income change of $500.00"],
    )


class _FakeAdvisor:
    def __init__(self, reply=None, error=None):
        self.reply = reply
        self.error = error
        self.calls = []

    def explain_scenario(self, month, scenario):
        self.calls.append((month, scenario))
        if self.error:
            raise self.error
        return self.reply


def _drain(presenter):
    presenter._task.join(timeout=2)
    presenter._task.poll(_FakeWidget())


def test_add_and_remove_adjustment():
    presenter = ScenarioPresenter()
    changes = []
    presenter.attach(on_change=lambda: changes.append(None))

    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")
    assert len(presenter.adjustments) == 1
    assert presenter.adjustments[0].label == "Raise"

    presenter.add_adjustment(AdjustmentType.EXTRA_DEBT_PAYMENT, 1000, "Extra payment")
    assert len(presenter.adjustments) == 2

    presenter.remove_adjustment(0)
    assert len(presenter.adjustments) == 1
    assert presenter.adjustments[0].label == "Extra payment"

    # attach() call + 3 mutations
    assert len(changes) == 4


def test_run_scenario_does_nothing_without_adjustments():
    calls = []
    presenter = ScenarioPresenter(run_scenario_fn=lambda month, scenario: calls.append(scenario))
    presenter.run_scenario()

    assert calls == []
    assert presenter.result is None


def test_run_scenario_builds_scenario_from_adjustments_and_stores_result():
    captured = {}

    def fake_run_scenario(month, scenario):
        captured["month"] = month
        captured["scenario"] = scenario
        return make_scenario_result(scenario)

    presenter = ScenarioPresenter(month="2026-06", run_scenario_fn=fake_run_scenario)
    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")

    presenter.run_scenario()

    assert captured["month"] == "2026-06"
    assert captured["scenario"].adjustments == presenter.adjustments
    assert presenter.result is not None
    assert presenter.narrative_state == NarrativeState.IDLE
    assert presenter.narrative_text is None


def test_running_a_new_scenario_resets_previous_narrative():
    presenter = ScenarioPresenter(run_scenario_fn=lambda month, s: make_scenario_result(s))
    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")
    presenter.run_scenario()

    presenter.narrative_state = NarrativeState.DONE
    presenter.narrative_text = "Old explanation"

    presenter.run_scenario()

    assert presenter.narrative_state == NarrativeState.IDLE
    assert presenter.narrative_text is None


def test_explain_with_ai_requires_a_result_first():
    advisor = _FakeAdvisor(reply="unused")
    presenter = ScenarioPresenter(advisor=advisor)

    presenter.explain_with_ai(_FakeWidget())

    assert advisor.calls == []
    assert presenter._task is None


def test_explain_with_ai_delivers_reply():
    presenter = ScenarioPresenter(
        run_scenario_fn=lambda month, s: make_scenario_result(s),
        advisor=_FakeAdvisor(reply="This looks like a solid plan."),
    )
    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")
    presenter.run_scenario()

    presenter.explain_with_ai(_FakeWidget())
    _drain(presenter)

    assert presenter.narrative_state == NarrativeState.DONE
    assert presenter.narrative_text == "This looks like a solid plan."


def test_explain_with_ai_error_becomes_friendly_message():
    presenter = ScenarioPresenter(
        run_scenario_fn=lambda month, s: make_scenario_result(s),
        advisor=_FakeAdvisor(error=ValueError("boom")),
    )
    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")
    presenter.run_scenario()

    presenter.explain_with_ai(_FakeWidget())
    _drain(presenter)

    assert presenter.narrative_state == NarrativeState.ERROR
    assert "boom" in presenter.narrative_text


def test_explain_with_ai_ignored_while_already_running():
    import threading

    release = threading.Event()

    class _BlockingAdvisor:
        def __init__(self):
            self.calls = 0

        def explain_scenario(self, month, scenario):
            self.calls += 1
            release.wait()
            return "Reply"

    advisor = _BlockingAdvisor()
    presenter = ScenarioPresenter(
        run_scenario_fn=lambda month, s: make_scenario_result(s), advisor=advisor
    )
    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")
    presenter.run_scenario()

    presenter.explain_with_ai(_FakeWidget())
    presenter.explain_with_ai(_FakeWidget())

    assert advisor.calls == 1

    release.set()
    _drain(presenter)


def test_reattaching_replays_via_immediate_on_change_call():
    presenter = ScenarioPresenter(run_scenario_fn=lambda month, s: make_scenario_result(s))
    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")
    presenter.run_scenario()
    presenter.detach()

    calls = []
    presenter.attach(on_change=lambda: calls.append(presenter.result))

    assert len(calls) == 1
    assert calls[0] is presenter.result


def test_dead_widget_callback_self_heals_instead_of_raising():
    # attach()'s own replay call happens while the view is guaranteed alive (it just
    # constructed itself), so only a *later* notify -- after the widget could plausibly
    # have been torn down -- should raise, mirroring the real <Destroy>-vs-scheduled-callback
    # race this guards against.
    presenter = ScenarioPresenter(
        run_scenario_fn=lambda month, s: make_scenario_result(s),
        advisor=_FakeAdvisor(reply="Reply"),
    )
    presenter.add_adjustment(AdjustmentType.INCOME_CHANGE, 500, "Raise")
    presenter.run_scenario()

    call_count = {"n": 0}

    def flaky_callback():
        call_count["n"] += 1
        if call_count["n"] > 1:
            raise tkinter.TclError('invalid command name ".!label"')

    presenter.attach(on_change=flaky_callback)

    presenter.explain_with_ai(_FakeWidget())
    _drain(presenter)  # must not raise

    assert presenter._on_change is None
