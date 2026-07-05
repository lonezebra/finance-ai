from finance_ai.ai.runtime import AIRuntime
from finance_ai.finance.briefing_summary import briefing_summary


class StrategicAdvisor:
    def __init__(self):
        self.runtime = AIRuntime()

    def executive_briefing(
        self,
        month: str = "2026-06",
    ) -> str:

        briefing = briefing_summary(month)

        return self.runtime.ask(
            prompt="executive_briefing",
            context=briefing,
        )