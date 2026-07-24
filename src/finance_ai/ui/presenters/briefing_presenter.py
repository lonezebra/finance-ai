from finance_ai.ai.advisor import StrategicAdvisor


class BriefingPresenter:
    def __init__(self):
        self.advisor = StrategicAdvisor()

    def get_briefing_text(self, month: str = "2026-06") -> str:
        return self.advisor.executive_briefing(month)
