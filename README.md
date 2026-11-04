# repository-level-benchmark

## Setup

Before running the benchmark, prepare one of the following:

- **OpenRouter:** sign up or sign in to OpenRouter, then create an API key on
  the [API keys page](https://openrouter.ai/settings/keys).
- **Local model:** install [llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/docs/install.md)
  (which provides `llama-server`) and download a GGUF model. See
  [Providers](#providers) for the server command.

Run these commands from the benchmark project:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run the benchmark

The `bench` command runs the benchmark against a model of your choice:

```sh
bench --provider openrouter --model provider/model
```

For OpenRouter, the command prompts for the API key without echoing it. The key
is kept in memory for the run and is not written to reports.

`bench` evaluates a selected model on the benchmark's bug cases. The model is
given repository-level context from the bundled repositories, told which file
contains a bug, and asked to return the corrected target file. The benchmark
replaces that file, runs the tests, and saves per-bug results.

A bug counts as fixed when its tests pass. With one attempt per bug, the
aggregate score is **pass@1**: the share of cases fixed successfully on the
first attempt.

When `bench` runs, it will automatically create a virtual environment inside
each repository's mutation copy and install its configured test dependencies.
The environment is preserved when that copy is refreshed for the next bug case.
Environments are created locally; they are not bundled with the repository
source.

## Providers

### OpenRouter

OpenRouter gives the benchmark access to remotely hosted models. You need an
OpenRouter API key. Inference runs on the provider's servers.

In a terminal opened in the benchmark project directory, activate the virtual
environment created during setup:

```sh
source .venv/bin/activate
```

Then start the benchmark:

```sh
bench --provider openrouter --model provider/model
```

Replace `provider/model` with the model ID from the
[OpenRouter model catalog](https://openrouter.ai/models). Enter your API key
when prompted.

### llama.cpp (local model)

With llama.cpp, inference runs on your machine. Start the model server first,
then run the benchmark in a separate terminal while the server stays running.

**Terminal 1 — start the model server:**

```sh
llama-server --model /path/to/model.gguf --host 127.0.0.1 --port 8080
```

Replace `/path/to/model.gguf` with the path to your downloaded GGUF model.
The host `127.0.0.1` and port `8080` are example values. You can choose a
different host or port, then use those same values in the benchmark's
`--base-url` below.
Wait until the server has loaded the model and is ready to accept requests.
Leave this terminal open for the entire benchmark run.

**Terminal 2 — run the benchmark:**

Open another terminal in the benchmark project directory and activate the
virtual environment created during setup:

```sh
source .venv/bin/activate
```

Then start the benchmark:

```sh
bench --provider llama-cpp --base-url http://127.0.0.1:8080/v1
```

The benchmark requires the full llama.cpp API base URL and lets the server use
its loaded model, so you do not need a `--model` argument or an OpenRouter API
key. If you change the server's host or port, update `--base-url` to match,
keeping the `/v1` suffix.

When the benchmark finishes, you can stop the server with `Ctrl+C` in Terminal 1.

## Request handling

The benchmark processes cases sequentially by default (`--threads 1`). Pass
`--threads N` to evaluate up to N repositories concurrently. Cases in the same
repository stay sequential because they share working files and a virtual
environment. Reports retain the original case order. Values below 1 are
rejected.

```sh
bench --provider llama-cpp --base-url http://127.0.0.1:8080/v1 --threads 4
```

When OpenRouter rate limits a request, it retries up to five total attempts with
exponential backoff, rather than counting each throttled attempt as a failed bug
fix.
