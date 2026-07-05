from finance_ai.ai.lmstudio_client import LMStudioClient
from finance_ai.finance.briefing_summary import briefing_summary


SYSTEM_PROMPT = """
You are Open CFO's Strategic Advisor.

You explain financial information clearly, practically, and conservatively.

Rules:
- Do not invent numbers.
- Use only the data provided.
- Explain tradeoffs.
- Be specific when the data supports it.
- If the data is incomplete, say so.
- Do not give legal or tax advice.
- Do not claim certainty about market returns.
""".strip()


class AIAdvisor:
    def __init__(self):
        self.client = LMStudioClient()

    def explain_briefing(self, month: str = "2026-06") -> str:
        briefing = briefing_summary(month)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
Here is the current Open CFO Executive Briefing:

{briefing}

Rewrite this as a concise CFO-style explanation for the user.
Focus on:
1. Overall financial position
2. Key risks
3. Highest-impact next move
4. Important caveats
""".strip(),
            },
        ]

        return self.client.chat(messages)