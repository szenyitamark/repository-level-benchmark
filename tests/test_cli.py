import contextlib
import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from src.__main__ import main


class CliTests(unittest.TestCase):
    def test_invalid_openrouter_key_is_reprompted_before_benchmark(self):
        unauthorized = HTTPError(
            "https://openrouter.ai/api/v1/auth/key",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b"invalid key"),
        )
        with (
            patch("src.__main__.getpass.getpass", side_effect=["wrong", "valid"]) as prompt,
            patch(
                "src.__main__.OpenRouter.validate_api_key",
                side_effect=[unauthorized, None],
            ),
            patch(
                "src.__main__.run_benchmark",
                return_value={"complete": True},
            ) as run_benchmark,
            contextlib.redirect_stderr(io.StringIO()) as stderr,
        ):
            result = main(["--provider", "openrouter", "--model", "provider/model"])

        self.assertEqual(result, 0)
        self.assertEqual(prompt.call_count, 2)
        run_benchmark.assert_called_once()
        self.assertIn("Invalid OpenRouter API key. Please try again.", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
