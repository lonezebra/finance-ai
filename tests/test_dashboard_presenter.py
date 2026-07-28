import tkinter

from sqlalchemy.exc import SQLAlchemyError

from finance_ai.finance.dashboard import DashboardData
from finance_ai.finance.metrics import FinancialSnapshot
from finance_ai.ui.presenters.dashboard_presenter import DashboardPresenter


def make_data() -> DashboardData:
    snapshot = FinancialSnapshot(
        month="2026-05",
        total_assets=100000.0,
        total_debt=20000.0,
        net_worth=80000.0,
        cash_balance=10000.0,
        monthly_income=5000.0,
        monthly_expenses=4000.0,
        monthly_cash_flow=1000.0,
        savings_rate=0.2,
        debt_to_income_ratio=0.1,
        emergency_fund_months=2.5,
    )
    return DashboardData(
        month="2026-05",
        snapshot=snapshot,
        accounts=[],
        debts=[],
        assets=[],
        recent_transactions=[],
        budget_lines=[],
    )


def make_presenter(**overrides) -> DashboardPresenter:
    defaults = {"create_dashboard_data_fn": lambda: make_data()}
    defaults.update(overrides)
    return DashboardPresenter(**defaults)


def test_attaching_loads_the_data_immediately():
    presenter = make_presenter()
    calls = []

    presenter.attach(on_change=lambda: calls.append(presenter.data))

    assert presenter.data == make_data()
    assert presenter.status is None
    assert len(calls) == 1


def test_a_read_failure_becomes_a_status_message_not_a_crash():
    def boom():
        raise SQLAlchemyError("database is locked")

    presenter = make_presenter(create_dashboard_data_fn=boom)
    presenter.attach(on_change=lambda: None)

    assert presenter.data is None
    assert presenter.status is not None
    assert presenter.status.is_error
    assert "database is locked" in presenter.status.text


def test_refresh_clears_a_previous_error_once_the_read_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise SQLAlchemyError("temporary")
        return make_data()

    presenter = make_presenter(create_dashboard_data_fn=flaky)
    presenter.attach(on_change=lambda: None)
    assert presenter.status.is_error

    presenter.refresh()

    assert presenter.status is None
    assert presenter.data == make_data()


def test_detaching_stops_notifications():
    presenter = make_presenter()
    calls = []
    presenter.attach(on_change=lambda: calls.append(1))
    presenter.detach()

    presenter.refresh()

    assert len(calls) == 1  # only the attach() call


def test_dead_widget_callback_self_heals_instead_of_raising():
    presenter = make_presenter()
    call_count = {"n": 0}

    def flaky():
        call_count["n"] += 1
        if call_count["n"] > 1:
            raise tkinter.TclError('invalid command name ".!label"')

    presenter.attach(on_change=flaky)

    presenter.refresh()  # must not raise

    assert presenter._on_change is None
