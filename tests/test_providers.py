import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from src.providers.llama_cpp import LlamaCpp
from src.providers.openrouter import OpenRouter


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def response(content: str) -> FakeResponse:
    return FakeResponse(
        json.dumps({"choices": [{"message": {"content": content}}]}).encode()
    )


class ProviderTests(unittest.TestCase):
    def test_openrouter_validates_key_with_auth_endpoint(self):
        with patch(
            "src.providers.openrouter.urllib.request.urlopen",
            return_value=response(""),
        ) as urlopen:
            OpenRouter("secret", "provider/model").validate_api_key()

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/auth/key")
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")

    def test_openrouter_sends_configured_bearer_key(self):
        with patch(
            "src.providers.openrouter.urllib.request.urlopen",
            return_value=response("fixed source"),
        ) as urlopen:
            result = OpenRouter("secret", "provider/model").complete("prompt")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(result, "fixed source\n")

    def test_openrouter_retries_rate_limits_with_backoff(self):
        rate_limit = HTTPError(
            "https://openrouter.ai/api/v1/chat/completions",
            429,
            "rate limited",
            {},
            io.BytesIO(b"rate limited"),
        )
        with (
            patch(
                "src.providers.openrouter.urllib.request.urlopen",
                side_effect=[rate_limit, response("fixed source")],
            ) as urlopen,
            patch("src.providers.openrouter.time.sleep") as sleep,
        ):
            result = OpenRouter("secret", "provider/model").complete("prompt")

        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)
        self.assertEqual(result, "fixed source\n")

    def test_llama_cpp_uses_openai_compatible_server(self):
        with patch(
            "src.providers.llama_cpp.urllib.request.urlopen",
            return_value=response("fixed source"),
        ) as urlopen:
            result = LlamaCpp(
                "http://localhost:8080/v1/",
                "local-secret",
            ).complete("prompt")

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "http://localhost:8080/v1/chat/completions",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer local-secret")
        request_body = json.loads(request.data)
        self.assertNotIn("model", request_body)
        self.assertEqual(request_body["messages"][-1]["content"], "prompt")
        self.assertEqual(result, "fixed source\n")


if __name__ == "__main__":
    unittest.main()
