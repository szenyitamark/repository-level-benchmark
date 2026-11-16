from dataclasses import dataclass


@dataclass
class CaseResult:
    case_id: str
    repository: str
    status: str
    error_type: str | None = None
    error_message: str | None = None
