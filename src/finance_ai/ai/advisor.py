from finance_ai.ai.runtime import AIRuntime
from finance_ai.reports.engine import create_executive_report
from finance_ai.reports.formatter import format_executive_report_for_ai
from finance_ai.scenario.engine import run_scenario
from finance_ai.scenario.formatter import format_scenario_for_ai
from finance_ai.scenario.models import Scenario


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

    def chat(
        self,
        month: str,
        messages: list[dict[str, str]],
    ) -> str:

        report = create_executive_report(month, persist=False)
        context = format_executive_report_for_ai(report)

        return self.runtime.chat(
            prompt="strategic_advisor",
            context=context,
            messages=messages,
        )

    def explain_scenario(
        self,
        month: str,
        scenario: Scenario,
    ) -> str:

        result = run_scenario(month, scenario)
        context = format_scenario_for_ai(result)

        return self.runtime.ask(
            prompt="scenario",
            context=context,
        )
