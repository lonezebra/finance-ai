# AI Architecture

## Philosophy

Open CFO separates deterministic financial intelligence from AI reasoning.

Python calculates.

Python structures.

AI reasons.

AI communicates.

---

## Responsibilities

### Finance Engine

Produces deterministic financial calculations.

### Decision Engine

Ranks financial decisions.

### Open CFO Engine

Builds structured Executive Reports.

### Strategic Advisor

Uses a local language model to explain the Executive Report, discuss tradeoffs, answer questions, and guide planning.

---

## AI Runtime

The AI Runtime is model-agnostic.

Responsibilities:

- Prompt loading
- Prompt versioning
- Context construction
- Model communication
- Thinking state
- Response generation

The runtime should not contain financial business logic.

---

## Prompt Library

Prompt assets live outside the source code.

```
assets/
    prompts/
```

Prompts are version-controlled and benchmarked independently of application code.

---

## Supported Models

Current focus:

- Gemma4 26B A4B (Daily Executive Briefing)
- Qwen 3.6 27B Dense (Deep Strategic Advisor)

Future:

- Additional local models through LM Studio

---

## Benchmark Philosophy

Model benchmarking is performed offline by developers.

Benchmarking should measure:

- Response quality
- Response time
- Financial reasoning
- Hallucination rate
- Recommendation usefulness

Benchmarking is not part of the runtime.

---

## Long-Term Vision

The AI Runtime should support multiple local providers without requiring changes to the Finance Engine or Open CFO Engine.