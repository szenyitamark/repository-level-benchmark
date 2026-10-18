import subprocess

from src.models.repository import Repository


def run_tests_mutated(
    repository: Repository,
) -> str:
    mutation_path = repository.get_mutation_path().resolve()

    try:
        result = subprocess.run(
            [repository.get_python_path(), *repository.test_command],
            cwd=mutation_path,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT"

    return "PASS" if result.returncode == 0 else "FAIL"
