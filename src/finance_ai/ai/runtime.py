from finance_ai.ai.lmstudio_client import LMStudioClient
from finance_ai.ai.prompt_library import PromptLibrary


class AIRuntime:
    def __init__(self):
        self.client = LMStudioClient()
        self.prompts = PromptLibrary()

    def ask(
        self,
        prompt: str,
        context: str,
        temperature: float = 0.4,
    ) -> str:

        system_prompt = self.prompts.load(prompt)

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": context,
            },
        ]

        return self.client.chat(
            messages,
            temperature=temperature,
        )

    def chat(
        self,
        prompt: str,
        context: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> str:
        """Multi-turn variant of ask(). context (e.g. the user's financial snapshot) doesn't
        change turn to turn, so it's folded into the system message once rather than repeated
        as a user turn; messages carries the growing user/assistant history."""

        role_prompt = self.prompts.load(prompt)
        system_prompt = f"{role_prompt}\n\n---\n\nCurrent Financial Context:\n\n{context}"

        full_messages = [{"role": "system", "content": system_prompt}, *messages]

        return self.client.chat(
            full_messages,
            temperature=temperature,
        )