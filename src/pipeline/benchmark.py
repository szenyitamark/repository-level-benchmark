import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.models.bug import Bug
from src.models.repository import Repository
from src.pipeline.bugs import load_bug_cases
from src.pipeline.cloner import prepare_repositories
from src.pipeline.mutator import mutate
from src.pipeline.tester import run_tests_mutated
from src.providers.base import CompletionProvider

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


@dataclass
class CaseResult:
    case_id: str
    repository: str
    status: str
    output: str


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
        "This repository contains one single bug in the target file Inspect the repository context and fix "
        "the bug in the target file. Return the complete corrected version of "
        "the target file and nothing else. Do not include tests, explanations, or Markdown.\n\n"
        f"Target file: {target_path}\n\n"
        f"Repository context:\n{repository_content}"
    )


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
    model: CompletionProvider,
    repository: Repository,
    bug: Bug,
) -> CaseResult:
    try:
        mutate(bug, repository)
        prompt = build_prompt(bug, read_repository(repository))
        fixed_source = model.complete(prompt)
        apply_fixed_source(repository, bug, fixed_source)
        test_result = run_tests_mutated(repository)
        return CaseResult(
            case_id=bug.case_id,
            repository=bug.repository_name,
            status=test_result.status,
            output=test_result.output,
        )
    except Exception as error:
        return CaseResult(
            case_id=bug.case_id,
            repository=bug.repository_name,
            status="ERROR",
            output=f"{type(error).__name__}: {error}",
        )


def run_benchmark(
    model_id: str,
    model: CompletionProvider,
    provider: str = "openrouter",
) -> dict[str, object]:
    repositories = prepare_repositories()
    repositories_by_name = {
        repository.get_name(): repository for repository in repositories
    }
    bugs = load_bug_cases()
    results = []

    for bug in bugs:
        result = evaluate_case(model, repositories_by_name[bug.repository_name], bug)
        results.append(result)
        print(f"{bug.case_id}: {result.status}")

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
