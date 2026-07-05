from dataclasses import dataclass
from enum import Enum


class ThinkingPhase(str, Enum):
    BUILD_CONTEXT = "Building financial context..."
    REVIEW_HEALTH = "Reviewing financial health..."
    REVIEW_CONFIDENCE = "Reviewing confidence score..."
    ANALYZE_DECISIONS = "Evaluating decision tradeoffs..."
    GENERATE_RESPONSE = "Generating strategic recommendation..."


@dataclass(frozen=True)
class ThinkingState:
    phase: ThinkingPhase
    progress: int


EXECUTIVE_BRIEFING_THINKING_STEPS = [
    ThinkingState(ThinkingPhase.BUILD_CONTEXT, 10),
    ThinkingState(ThinkingPhase.REVIEW_HEALTH, 30),
    ThinkingState(ThinkingPhase.REVIEW_CONFIDENCE, 50),
    ThinkingState(ThinkingPhase.ANALYZE_DECISIONS, 75),
    ThinkingState(ThinkingPhase.GENERATE_RESPONSE, 95),
]