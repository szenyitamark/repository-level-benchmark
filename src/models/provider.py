from abc import ABC, abstractmethod


class Provider(ABC):
    timeout: int = 300

    @abstractmethod
    def complete(self, prompt: str) -> str:
        raise NotImplementedError
