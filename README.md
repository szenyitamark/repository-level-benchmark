# repository-level-benchmark

## Command

The benchmark has one command: `bench`.

Run it from the benchmark project:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
bench --provider openrouter --model provider/model
```

For OpenRouter, the command prompts for the API key without echoing it. The
key is kept in memory for the run and is not written to reports.

`bench` evaluates a selected model on the benchmark's bug cases. The model is
given repository-level context from the bundled repositories, told which file
contains a bug, and asked to return the corrected target file. The benchmark
replaces that file, runs the tests, and saves per-bug results.

A bug counts as fixed when its tests pass. With one attempt per bug, the
aggregate score is **pass@1**: the share of cases fixed successfully on the
first attempt.

When `bench` runs, it will automatically create a virtual environment inside
each repository's mutation copy and install its configured test dependencies.
The environment is preserved when that copy is refreshed for the next bug
case. Environments are created locally; they are not bundled with the
repository source.

## Providers

OpenRouter is selected with `--provider openrouter` and a model ID. To use a
local model, start a llama.cpp server and pass its API URL:

```sh
llama-server --model /path/to/model.gguf --host 127.0.0.1 --port 8080
bench --provider llama-cpp --base-url http://127.0.0.1:8080/v1
```

The benchmark requires the full llama.cpp API base URL and lets the server use
its loaded model. The llama.cpp provider does not send authentication headers.

## Request handling

The benchmark processes cases sequentially by default (`--threads 1`). Pass
`--threads N` to evaluate up to N repositories concurrently. Cases in the same
repository stay sequential because they share working files and a virtual
environment. Reports retain the original case order. Values below 1 are rejected.

```sh
bench --provider llama-cpp --base-url http://127.0.0.1:8080/v1 --threads 4
```

When OpenRouter rate limits a
request, it retries up to five total attempts with exponential backoff, rather
than counting each throttled attempt as a failed bug fix.
