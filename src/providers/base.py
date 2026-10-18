from typing import Protocol


class CompletionProvider(Protocol):
    def complete(self, prompt: str, timeout: int = 180) -> str: ...
