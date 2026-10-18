import argparse
import getpass
import json
import os
import sys
import urllib.error
from pathlib import Path

from src.models.llama_cpp import LlamaCpp
from src.models.openrouter import OpenRouter
from src.pipeline.benchmark import run_benchmark

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benchmark")
    parser.description = "Run the repository-level bug-fix benchmark."
    parser.add_argument(
        "--model",
        help="OpenRouter model ID",
    )
    parser.add_argument(
        "--provider",
        choices=["openrouter", "llama-cpp"],
        default="openrouter",
        help="model provider",
    )
    parser.add_argument(
        "--base-url",
        help="llama.cpp API base URL, e.g. http://127.0.0.1:8080/v1",
    )
    arguments = parser.parse_args(argv)

    os.chdir(ROOT)
    if arguments.provider == "openrouter":
        if not arguments.model or not arguments.model.strip():
            parser.error("--model is required for the openrouter provider")
        if arguments.base_url is not None:
            parser.error("--base-url can only be used with the llama-cpp provider")
        model_id = arguments.model.strip()
        while True:
            api_key = getpass.getpass("OpenRouter API key: ").strip()
            if not api_key:
                print("An OpenRouter API key is required.", file=sys.stderr)
                return 2
            model = OpenRouter(api_key, model_id)
            try:
                model.validate_api_key()
            except urllib.error.HTTPError as error:
                error.read()
                error.close()
                if error.code != 401:
                    print(
                        f"OpenRouter API key validation failed with HTTP "
                        f"{error.code}: {error.reason}",
                        file=sys.stderr,
                    )
                    return 1
                print("Invalid OpenRouter API key. Please try again.", file=sys.stderr)
            except OSError as error:
                print(
                    f"Could not validate OpenRouter API key: {error}", file=sys.stderr
                )
                return 1
            else:
                break
    else:
        if not arguments.base_url or not arguments.base_url.strip():
            parser.error("--base-url is required for the llama-cpp provider")
        base_url = arguments.base_url.strip().rstrip("/")
        model_id = f"llama.cpp@{base_url}"
        model = LlamaCpp(base_url)
    try:
        report = run_benchmark(model_id, model, arguments.provider)
    except (
        KeyError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(f"Benchmark could not run: {error}", file=sys.stderr)
        return 1

    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
