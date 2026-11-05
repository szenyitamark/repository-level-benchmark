import json
import time
import urllib.error
import urllib.request

from src.models.provider import Provider


class OpenRouter(Provider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def validate_api_key(self, timeout: int = 30) -> None:
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout):
            pass

    def validate_model(self, timeout: int = 30) -> None:
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not any(model["id"] == self.model for model in data["data"]):
            raise ValueError(
                f"Unknown OpenRouter model '{self.model}'. "
                "Choose a model ID from https://openrouter.ai/models "
                "and pass it with --model."
            )

    def complete(self, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Fix the bug in the target file. Respond using exactly "
                            "these sections: Reasoning: followed by a concise explanation, "
                            "then Fix: followed by the complete corrected target-file "
                            "contents. The fix should include nothing but the exact code to be placed in the target file"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        retry_number = 1
        while True:
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as error:
                if error.code != 429 or retry_number == 5:
                    raise
                error.read()
                delay = 2 ** (retry_number - 1)
                print(f"OpenRouter rate limited the request; retrying in {delay:g}s.")
                time.sleep(delay)
                retry_number += 1

        return data["choices"][0]["message"]["content"].strip() + "\n"
