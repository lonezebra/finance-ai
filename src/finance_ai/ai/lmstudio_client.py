from openai import OpenAI

from finance_ai.config import (
    LM_STUDIO_API_KEY,
    LM_STUDIO_BASE_URL,
    LM_STUDIO_MODEL,
)


class LMStudioClient:
    def __init__(self):
        self.client = OpenAI(
            base_url=LM_STUDIO_BASE_URL,
            api_key=LM_STUDIO_API_KEY,
        )

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        response = self.client.chat.completions.create(
            model=LM_STUDIO_MODEL,
            messages=messages,
            temperature=temperature,
        )

        return response.choices[0].message.content or ""