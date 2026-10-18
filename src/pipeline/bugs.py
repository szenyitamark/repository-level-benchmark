import json
from pathlib import Path

from src.models.bug import Bug

ROOT = Path(__file__).resolve().parents[2]


def load_bug_cases() -> list[Bug]:
    bugs: list[Bug] = []

    for bug_path in sorted((ROOT / "bugs").glob("*.json")):
        data = json.loads(bug_path.read_text(encoding="utf-8"))
        file_path = Path(data["file_path"])
        repository_name = file_path.parts[2]

        bugs.append(
            Bug(
                case_id=bug_path.stem,
                repository_name=repository_name,
                file_path=file_path,
                original_source=data["original_source"],
                bug_injected_source=data["bug_injected_source"],
            )
        )

    return bugs
