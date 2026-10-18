import json
import urllib.request

from src.providers.provider import Provider


class LlamaCpp(Provider):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def complete(self, prompt: str) -> str:
        body = json.dumps(
            {
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
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip() + "\n"
