from dataclasses import dataclass


@dataclass
class CaseResult:
    case_id: str
    repository: str
    status: str
