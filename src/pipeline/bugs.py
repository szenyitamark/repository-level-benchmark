import json
from pathlib import Path

from src.models.bug import Bug
from src.models.repository import Repository

ROOT = Path(__file__).resolve().parents[2]


def load_bug_cases(repositories: list[Repository]) -> list[Bug]:
    repositories_by_name = {repository.get_name(): repository for repository in repositories}
    bugs: list[Bug] = []

    for bug_path in sorted((ROOT / "bugs").glob("*.json")):
        data = json.loads(bug_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Bug case must be a JSON object: {bug_path}")

        file_path = Path(data["file_path"])
        if (
            file_path.is_absolute()
            or ".." in file_path.parts
            or len(file_path.parts) < 4
            or file_path.parts[:2] != ("repositories", "original")
        ):
            raise ValueError(f"Invalid target file path in {bug_path}: {file_path}")

        repository_name = file_path.parts[2]
        if repository_name not in repositories_by_name:
            raise ValueError(
                f"Bug case {bug_path} references unknown repository "
                f"{repository_name!r}"
            )

        bugs.append(
            Bug(
                case_id=bug_path.stem,
                repository_name=repository_name,
                file_path=file_path,
                original_source=data["original_source"],
                bug_injected_source=data["bug_injected_source"],
            )
        )

    if not bugs:
        raise ValueError(f"No bug cases found under {ROOT / 'bugs'}")
    return bugs
