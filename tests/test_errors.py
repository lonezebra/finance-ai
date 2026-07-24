import httpx
import openai

from finance_ai.ai.errors import describe_ai_error


def test_describe_ai_error_for_connection_failure():
    exc = openai.APIConnectionError(
        request=httpx.Request("POST", "http://localhost:1234/v1/chat/completions")
    )

    message = describe_ai_error(exc)

    assert "LM Studio" in message
    assert "running" in message


def test_describe_ai_error_for_generic_exception():
    message = describe_ai_error(ValueError("unexpected"))

    assert "unexpected" in message
