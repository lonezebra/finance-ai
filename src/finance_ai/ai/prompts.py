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


def executive_briefing_prompt(briefing: str) -> str:
    return f"""
Here is the current Open CFO Executive Briefing:

{briefing}

Rewrite this as a concise CFO-style explanation for the user.

Focus on:
1. Overall financial position
2. Key risks
3. Highest-impact next move
4. Important caveats
""".strip()