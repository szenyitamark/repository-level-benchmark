from abc import ABC, abstractmethod


class Provider(ABC):
    timeout: int = 180

    @abstractmethod
    def complete(self, prompt: str) -> str:
        raise NotImplementedError
