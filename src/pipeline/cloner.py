import json
import subprocess
from pathlib import Path

from src.models.repository import Repository


def load_repositories() -> list[Repository]:
    repositories_path = Path("repositories/repositories.json")

    with repositories_path.open(encoding="utf-8") as file:
        repositories_data: list[dict] = json.load(file)

    repositories: list[Repository] = []

    for repository_data in repositories_data:
        repository = Repository(
            github_url=repository_data["github_url"],
            path=Path(repository_data["path"]),
            test_command=repository_data["test_command"],
            dependency_command=repository_data["dependency_command"],
        )
        repositories.append(repository)

    return repositories


def setup_venvs(repositories: list[Repository]) -> None:
    for repository in repositories:
        if repository.get_venv_path().exists():
            continue

        subprocess.run(
            ["python", "-m", "venv", repository.get_venv_path()],
            check=True,
        )

        subprocess.run(
            [repository.get_pip_path(), "install", *repository.dependency_command],
            cwd=repository.get_original_root(),
            check=True,
        )
