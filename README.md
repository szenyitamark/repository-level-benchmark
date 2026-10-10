# repository-level-benchmark

## Command

The benchmark has one command: `bench`.

`bench` evaluates a selected model on the benchmark's bug cases. The model is
given repository-level context from the bundled repositories, told which file
contains a bug, and asked to return the corrected target file. The benchmark
replaces that file, runs the tests, and saves per-bug results.

A bug counts as fixed when its tests pass. With one attempt per bug, the
aggregate score is **pass@1**: the share of cases fixed successfully on the
first attempt.

## Model compatibility

The initial model provider will be **OpenRouter**. Users will provide their
API key and choose a model ID; the benchmark will display request errors,
including invalid or unavailable model errors.

The design should allow **llama.cpp** as a future local-model provider without
making the rest of the benchmark depend on which provider is selected.

## Request handling

The initial implementation will process cases sequentially. When OpenRouter
rate limits a request, the benchmark must honor the `Retry-After` header before
retrying, rather than counting the throttled request as a failed bug fix.
