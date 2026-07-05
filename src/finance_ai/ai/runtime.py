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