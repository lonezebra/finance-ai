from finance_ai.ai.runtime import AIRuntime
from finance_ai.reports.engine import create_executive_report
from finance_ai.reports.formatter import format_executive_report_for_ai


class StrategicAdvisor:
    def __init__(self):
        self.runtime = AIRuntime()

    def executive_briefing(
        self,
        month: str = "2026-06",
    ) -> str:

        report = create_executive_report(month)
        context = format_executive_report_for_ai(report)

        return self.runtime.ask(
            prompt="executive_briefing",
            context=context,
        )
