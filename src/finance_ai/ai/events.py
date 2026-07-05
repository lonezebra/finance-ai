from dataclasses import dataclass


@dataclass(frozen=True)
class AIEvent:
    event: str
    payload: dict