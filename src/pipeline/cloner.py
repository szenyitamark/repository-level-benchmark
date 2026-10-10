import subprocess

from src.models.repository import Repository


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
