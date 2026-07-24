import openai


def describe_ai_error(exc: Exception) -> str:
    if isinstance(exc, openai.APIConnectionError):
        return (
            "Could not reach LM Studio. Make sure LM Studio is running with a model "
            "loaded at http://localhost:1234/v1, then try again."
        )

    return f"Something went wrong while generating the briefing: {exc}"
