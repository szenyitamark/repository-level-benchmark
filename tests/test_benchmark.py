import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.models.bug import Bug
from src.pipeline.benchmark import build_prompt, read_repository


class BuildPromptTests(unittest.TestCase):
    def test_maps_original_bug_path_to_repository_relative_target(self):
        bug = Bug(
            case_id="aiosignal_1",
            repository_name="aiosignal",
            file_path=Path(
                "repositories/original/aiosignal/aiosignal/__init__.py"
            ),
            original_source="",
            bug_injected_source="",
        )

        prompt = build_prompt(bug, "repository context")

        self.assertIn("Target file: aiosignal/__init__.py", prompt)
        self.assertIn("Repository context:\nrepository context", prompt)

    def test_repository_context_includes_tests_but_excludes_caches(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            (repository_root / "src").mkdir()
            (repository_root / "tests").mkdir()
            (repository_root / ".venv").mkdir()
            (repository_root / "src" / "module.py").write_text(
                "source code",
                encoding="utf-8",
            )
            (repository_root / "tests" / "test_module.py").write_text(
                "test code",
                encoding="utf-8",
            )
            (repository_root / ".venv" / "ignored.py").write_text(
                "environment code",
                encoding="utf-8",
            )
            repository = SimpleNamespace(
                get_mutation_root=lambda: repository_root,
            )

            context = read_repository(repository)

        self.assertIn("--- tests/test_module.py ---\ntest code", context)
        self.assertIn("--- src/module.py ---\nsource code", context)
        self.assertNotIn("environment code", context)


if __name__ == "__main__":
    unittest.main()
