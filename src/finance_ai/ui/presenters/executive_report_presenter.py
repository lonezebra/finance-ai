from finance_ai.reports.engine import create_executive_report
from finance_ai.reports.models import ExecutiveReport


class ExecutiveReportPresenter:
    """Read path for the briefing's summary cards.

    Uses persist=False -- cards render on every page visit, and must not write a new
    financial_snapshot_records row just from being viewed. Only "Generate Briefing"
    (StrategicAdvisor.executive_briefing) persists a snapshot, since clicking it is a
    deliberate check-in.
    """

    def get_report(self, month: str = "2026-06") -> ExecutiveReport:
        return create_executive_report(month, persist=False)
