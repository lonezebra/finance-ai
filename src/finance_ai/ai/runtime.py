from finance_ai.ai.lmstudio_client import LMStudioClient
from finance_ai.ai.prompts import SYSTEM_PROMPT, executive_briefing_prompt
from finance_ai.finance.briefing_summary import briefing_summary


class AIRuntime:
    def __init__(self):
        self.client = LMStudioClient()

    def generate_executive_briefing(self, month: str = "2026-06") -> str:
        briefing = briefing_summary(month)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": executive_briefing_prompt(briefing)},
        ]

        return self.client.chat(messages)