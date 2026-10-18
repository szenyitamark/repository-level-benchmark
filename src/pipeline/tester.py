import subprocess
from dataclasses import dataclass

from src.models.repository import Repository


@dataclass
class TestResult:
    status: str
    output: str


def run_tests_mutated(
    repository: Repository,
    timeout: int = 120,
) -> TestResult:
    mutation_path = repository.get_mutation_path().resolve()

    try:
        result = subprocess.run(
            [repository.get_python_path(), *repository.test_command],
            cwd=mutation_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        return TestResult("TIMEOUT", output + stderr)

    output = result.stdout + result.stderr
    return TestResult("PASS" if result.returncode == 0 else "FAIL", output)
