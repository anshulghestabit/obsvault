from dataclasses import dataclass


@dataclass
class Day3Task:
    query: str


@dataclass
class FileInspection:
    query: str
    intent: str
    file_path: str
    output_path: str
    exists: bool
    file_type: str
    requested_items: int
    summary: str


@dataclass
class DBInspection:
    query: str
    intent: str
    file_path: str
    output_path: str
    file_type: str
    requested_items: int
    columns: list[str]
    preview: list[dict]
    db_path: str
    table_name: str
    summary: str


@dataclass
class CodeResult:
    final_answer: str
    raw_metrics: dict
    execution_log: str


@dataclass
class OrchestratedResult:
    route: str
    file_summary: str
    db_summary: str
    db_preview: list[dict]
    code_agent_answer: str
    final_answer: str
    execution_log: str
    intent: str