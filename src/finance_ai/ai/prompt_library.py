from pathlib import Path


class PromptLibrary:
    def __init__(self):
        self.prompt_dir = (
            Path(__file__).resolve().parents[3]
            / "assets"
            / "prompts"
        )

    def load(self, prompt_name: str) -> str:
        prompt_file = self.prompt_dir / f"{prompt_name}.md"

        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Prompt '{prompt_name}' does not exist."
            )

        return prompt_file.read_text(encoding="utf-8")