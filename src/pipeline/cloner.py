import json
import os
import subprocess
import sys
from pathlib import Path

from src.models.repository import Repository
from src.pipeline.mutator import copy_repository

SOURCE_VERSIONS = {
    "iniconfig": "2.3.1.dev7+g00e7d87c7",
    "pluggy": "1.6.1.dev222+gf91048bed",
    "python-discovery": "1.6.2.dev3+gb4eea32e5",
    "pytest-repeat": "0.9.4",
}


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
        copy_repository(repository)
        venv_path = repository.get_venv_path()
        setup_marker = venv_path / ".benchmark-setup-complete"
        if setup_marker.exists():
            continue

        if not venv_path.exists():
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

        environment = os.environ.copy()
        if version := SOURCE_VERSIONS.get(repository.get_name()):
            environment["SETUPTOOLS_SCM_PRETEND_VERSION"] = version

        subprocess.run(
            [
                repository.get_pip_path(),
                "install",
                *repository.dependency_command,
            ],
            cwd=repository.get_mutation_root(),
            check=True,
            env=environment,
        )
        setup_marker.touch()


def prepare_repositories() -> list[Repository]:
    repositories = load_repositories()
    setup_venvs(repositories)
    return repositories
