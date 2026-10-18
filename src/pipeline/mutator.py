import shutil
from pathlib import Path

from src.models.bug import Bug
from src.models.repository import Repository


def copy_repository(repository: Repository) -> None:
    shutil.copytree(
        repository.get_original_root(),
        repository.get_mutation_root(),
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
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
        ),
    )


def mutate_repository(bug: Bug, source_from: str, source_to: str) -> None:
    bug_mutation_path = Path(
        str(bug.file_path).replace(
            "repositories/original/",
            "repositories/mutation/",
            1,
        )
    )

    source: str = bug_mutation_path.read_text(encoding="utf-8")

    mutated_source: str = source.replace(
        source_from,
        source_to,
        1,
    )

    bug_mutation_path.write_text(
        mutated_source,
        encoding="utf-8",
    )


def mutate(bug: Bug, repository: Repository) -> None:
    copy_repository(repository)
    mutate_repository(bug, bug.original_source, bug.bug_injected_source)
