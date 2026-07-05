from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    name: str
    role: str
    notes: str


RECOMMENDED_MODELS = [
    ModelProfile(
        name="Gemma4 26B A4B",
        role="Daily Executive Briefing",
        notes="Fast and strong for concise CFO-style summaries.",
    ),
    ModelProfile(
        name="Qwen 3.6 27B Dense",
        role="Deep Strategic Advisor",
        notes="Slower, but useful for deeper reasoning and scenario discussion.",
    ),
    ModelProfile(
        name="9B-class model",
        role="Fast fallback",
        notes="Useful when speed matters more than depth.",
    ),
]