from dataclasses import dataclass
from pathlib import Path


@dataclass
class Bug:
    case_id: str
    repository_name: str
    file_path: Path
    original_source: str
    bug_injected_source: str
