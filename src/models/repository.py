import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Repository:
    github_url: str
    path: Path
    test_command: list[str]
    dependency_command: list[str]

    def get_name(self) -> str:
        return self.github_url.split("/")[-1].removesuffix(".git")

    def get_original_root(self) -> Path:
        return Path("repositories/original") / self.get_name()

    def get_mutation_root(self) -> Path:
        return Path("repositories/mutation") / self.get_name()

    def get_original_path(self) -> Path:
        return self.get_original_root() / self.path

    def get_mutation_path(self) -> Path:
        return self.get_mutation_root() / self.path

    def get_venv_path(self) -> Path:
        return self.get_mutation_root() / ".venv"

    def get_pip_path(self) -> Path:
        scripts = "Scripts" if sys.platform == "win32" else "bin"
        pip = "pip.exe" if sys.platform == "win32" else "pip"
        return (self.get_venv_path() / scripts / pip).resolve()

    def get_python_path(self) -> Path:
        scripts = "Scripts" if sys.platform == "win32" else "bin"
        python = "python.exe" if sys.platform == "win32" else "python"
        return (self.get_venv_path() / scripts / python).absolute()
