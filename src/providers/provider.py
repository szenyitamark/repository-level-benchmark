from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def complete(self, prompt: str, timeout: int = 180) -> str:
        raise NotImplementedError
