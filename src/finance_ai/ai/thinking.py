from dataclasses import dataclass


@dataclass(frozen=True)
class ThinkingStep:
    label: str


EXECUTIVE_BRIEFING_THINKING_STEPS = [
    ThinkingStep("Building financial context..."),
    ThinkingStep("Reviewing financial health..."),
    ThinkingStep("Reviewing confidence score..."),
    ThinkingStep("Evaluating top opportunities..."),
    ThinkingStep("Writing CFO-style briefing..."),
]