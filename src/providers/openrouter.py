import json
import time
import urllib.error
import urllib.request


def _retry_delay(retry_number: int) -> float:
    return min(2**retry_number, 30)


class OpenRouter:
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

    def complete(self, prompt: str, timeout: int = 180) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Fix the bug in the target file. Return only the "
                            "complete corrected target-file contents. Do not "
                            "include Markdown fences or explanations."
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

        for retry_number in range(5):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as error:
                if error.code != 429 or retry_number == 4:
                    raise
                error.read()
                delay = _retry_delay(retry_number)
                print(f"OpenRouter rate limited the request; retrying in {delay:g}s.")
                time.sleep(delay)

        return data["choices"][0]["message"]["content"].strip() + "\n"
