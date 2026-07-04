from finance_ai.finance.briefing_summary import briefing_summary


class BriefingPresenter:
    def get_briefing_text(self, month: str = "2026-06") -> str:
        return briefing_summary(month)