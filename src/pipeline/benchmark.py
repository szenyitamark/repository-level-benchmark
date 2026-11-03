import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from src.models.bug import Bug
from src.models.case_result import CaseResult
from src.models.llama_cpp import LlamaCpp
from src.models.openrouter import OpenRouter
from src.models.provider import Provider
from src.models.repository import Repository
from src.pipeline.bug_loader import load_bug_cases
from src.pipeline.cloner import prepare_repositories
from src.pipeline.mutator import mutate
from src.pipeline.tester import run_tests_mutated

EXCLUDED_DIRECTORIES = {
    ".git",
    ".hypothesis",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "site-packages",
}
ROOT = Path(__file__).resolve().parents[2]


def read_repository(repository: Repository) -> str:
    sections = []
    repository_root = repository.get_mutation_root()
    for file_path in sorted(repository_root.rglob("*")):
        relative_path = file_path.relative_to(repository_root)
        if (
            file_path.is_file()
            and file_path.suffix == ".py"
            and not any(part in EXCLUDED_DIRECTORIES for part in relative_path.parts)
        ):
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            sections.append(f"--- {relative_path} ---\n{content}")
    return "\n\n".join(sections)


def build_prompt(bug: Bug, repository_content: str) -> str:
    target_path = bug.file_path.relative_to(
        Path("repositories/original") / bug.repository_name
    )
    return (
        "This repository contains one single bug in the target file. Inspect the repository context and fix "
        "the bug in the target file.\n\n"
        "Use exactly this response format:\n"
        "Reasoning:\n"
        "A concise explanation of the bug and the chosen fix.\n"
        "Fix:\n"
        "The complete corrected contents of the target file.\n\n"
        f"Target file: {target_path}\n\n"
        f"Repository context:\n{repository_content}"
    )


def extract_fix(source: str) -> str:
    lines = source.strip().splitlines()
    fix_start = next(
        (index + 1 for index, line in enumerate(lines) if line.strip() == "Fix:"),
        None,
    )
    if fix_start is None:
        raise ValueError("Model response is missing the required Fix: section")

    fix_lines = lines[fix_start:]
    if fix_lines and fix_lines[0].strip() == "":
        fix_lines = fix_lines[1:]
    fix_source = "\n".join(fix_lines).strip()
    fence_lines = fix_source.splitlines()
    if (
        len(fence_lines) >= 2
        and fence_lines[0].startswith("```")
        and fence_lines[-1].strip() == "```"
    ):
        fix_source = "\n".join(fence_lines[1:-1]).strip()
    return fix_source + "\n"


def apply_fixed_source(repository: Repository, bug: Bug, fixed_source: str) -> None:
    target = (
        ROOT
        / repository.get_mutation_root()
        / bug.file_path.relative_to(repository.get_original_root())
    ).resolve()
    if not fixed_source.strip():
        raise ValueError("Model returned empty target-file source")
    target.write_text(fixed_source, encoding="utf-8")


def evaluate_case(
    model: Provider,
    repository: Repository,
    bug: Bug,
) -> CaseResult:
    try:
        mutate(bug, repository)
        prompt = build_prompt(bug, read_repository(repository))
        fixed_source = extract_fix(model.complete(prompt))
        apply_fixed_source(repository, bug, fixed_source)
        test_result = run_tests_mutated(repository)
        return CaseResult(
            case_id=bug.case_id,
            repository=bug.repository_name,
            status=test_result,
        )
    except Exception:
        return CaseResult(
            case_id=bug.case_id,
            repository=bug.repository_name,
            status="ERROR",
        )


def run_benchmark(
    model: Provider,
    threads: int = 1,
) -> dict[str, object]:
    if threads < 1:
        raise ValueError("threads must be at least 1")
    if isinstance(model, OpenRouter):
        provider = "openrouter"
        model_id = model.model
    elif isinstance(model, LlamaCpp):
        provider = "llama-cpp"
        model_id = "llama.cpp model"
    else:
        raise TypeError(f"Unsupported provider type: {type(model).__name__}")

    repositories = prepare_repositories()
    repositories_by_name = {
        repository.get_name(): repository for repository in repositories
    }
    bugs = load_bug_cases()
    results = []

    def evaluate_and_print(bug: Bug) -> CaseResult:
        result = evaluate_case(
            model,
            repositories_by_name[bug.repository_name],
            bug,
        )
        print(f"{bug.case_id}: {result.status}", flush=True)
        return result

    if threads == 1:
        results = [evaluate_and_print(bug) for bug in bugs]
    else:
        # Each repository owns a shared mutation copy and virtual environment.
        # Keep its cases in one worker so they cannot overwrite each other.
        groups: dict[str, list[Bug]] = {}
        for bug in bugs:
            groups.setdefault(bug.repository_name, []).append(bug)

        def evaluate_repository(cases: list[Bug]) -> list[CaseResult]:
            return [evaluate_and_print(bug) for bug in cases]

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [
                executor.submit(evaluate_repository, cases)
                for cases in groups.values()
            ]
            for future in as_completed(futures):
                results.extend(future.result())
        case_order = {bug.case_id: index for index, bug in enumerate(bugs)}
        results.sort(key=lambda result: case_order[result.case_id])

    passed = sum(result.status == "PASS" for result in results)
    failed = sum(result.status == "FAIL" for result in results)
    errors = sum(result.status == "ERROR" for result in results)
    complete = len(results) == len(bugs)
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "provider": provider,
        "model": model_id,
        "complete": complete,
        "summary": {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "attempted": len(results),
            "total": len(bugs),
            "pass@1_percent": (
                round(passed / len(bugs) * 100, 2) if complete else None
            ),
        },
        "results": [
            {key: value for key, value in asdict(result).items() if value is not None}
            for result in results
        ],
    }
    report_directory = ROOT / ".benchmark" / "reports"
    report_directory.mkdir(parents=True, exist_ok=True)
    report_path = report_directory / (
        "bench-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
    )
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Summary: {passed} passed, {failed} failed, {errors} errors; "
        f"{len(results)}/{len(bugs)} attempted."
    )
    if complete:
        print(f"pass@1: {report['summary']['pass@1_percent']}%")
    else:
        print("pass@1: unavailable because the run was incomplete.")
    print(f"Report: {report_path}")
    return report
