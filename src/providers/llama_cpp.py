import json
import urllib.request

from src.providers.provider import Provider


class LlamaCpp(Provider):
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

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
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip() + "\n"
