from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NexusTask:
    query: str


@dataclass
class PlanStep:
    step_id: int
    title: str
    owner: str
    instruction: str
    depends_on: list[int] = field(default_factory=list)
    can_run_parallel: bool = False
    fallback_owners: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    expected_output: str = ""
    success_checks: list[str] = field(default_factory=list)
    priority: int = 1
    max_retries: int = 1


@dataclass
class PlanResult:
    steps: list[PlanStep]
    planning_notes: str
    task_type: str
    target_file: str
    output_path: str


@dataclass
class WorkerInput:
    original_query: str
    step: PlanStep
    memory_context: str
    task_type: str
    target_file: str
    output_path: str


@dataclass
class WorkerOutput:
    step_id: int
    owner: str
    title: str
    result: str
    artifacts: dict[str, Any]
    status: str = "success"
    confidence: float = 0.75
    tool_calls: list[str] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)
    grounding_sources: list[str] = field(default_factory=list)
    artifacts_created: list[str] = field(default_factory=list)
    needs_handoff: bool = False
    handoff_target: str = ""
    retry_hint: str = ""


@dataclass
class CritiqueInput:
    query: str
    task_type: str
    plan: list[PlanStep]
    worker_outputs: list[WorkerOutput]


@dataclass
class CritiqueResult:
    critique: str
    risks: list[str]


@dataclass
class OptimizationInput:
    query: str
    task_type: str
    worker_outputs: list[WorkerOutput]
    critique: str


@dataclass
class OptimizationResult:
    improved_draft: str
    improvements: list[str]


@dataclass
class ArtifactRequirement:
    name: str
    path_hint: str = ""
    format: str = ""
    must_exist: bool = True
    description: str = ""


@dataclass
class ArtifactRecord:
    name: str
    path: str
    exists: bool
    size_bytes: int
    created_by: str
    status: str


@dataclass
class FulfillmentContract:
    task_summary: str
    deliverable_mode: str
    requested_output_path: str
    requested_folder: str
    must_create_new_folder: bool = False
    structural_requirements: list[str] = field(default_factory=list)
    count_requirements: dict[str, int] = field(default_factory=dict)
    expected_sections: list[str] = field(default_factory=list)
    min_depth_chars: int = 300
    artifact_requirements: list[ArtifactRequirement] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class ContractRequest:
    query: str
    task_type: str
    output_path: str


@dataclass
class CompletionCheckInput:
    query: str
    task_type: str
    draft: str
    worker_outputs: list[WorkerOutput]
    plan: list[PlanStep]
    contract: FulfillmentContract


@dataclass
class CompletionCheckResult:
    fulfilled: bool
    missing_requirements: list[str]
    satisfied_requirements: list[str]
    artifact_records: list[ArtifactRecord]
    task_satisfaction: dict[str, bool]
    summary: str


@dataclass
class ToolBuildInput:
    query: str
    task_type: str
    missing_capability: str
    contract: FulfillmentContract
    output_dir: str = "generated_tools"


@dataclass
class ToolBuildResult:
    built: bool
    tool_name: str
    file_path: str
    purpose: str
    import_hint: str
    smoke_test_passed: bool
    error: str = ""


@dataclass
class ValidationInput:
    query: str
    task_type: str
    draft: str
    worker_outputs: list[WorkerOutput]
    plan: list[PlanStep] = field(default_factory=list)
    contract: FulfillmentContract | None = None
    completion: CompletionCheckResult | None = None


@dataclass
class ValidationResult:
    passed: bool
    issues: list[str]
    validated_answer: str
    score: float = 0.0
    needs_retry: bool = False
    retry_targets: list[str] = field(default_factory=list)
    artifact_checks: dict[str, Any] = field(default_factory=dict)
    grounding_checks: dict[str, Any] = field(default_factory=dict)
    completeness_checks: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportInput:
    query: str
    task_type: str
    plan: list[PlanStep]
    worker_outputs: list[WorkerOutput]
    critique: str
    improvements: list[str]
    validated_answer: str
    contract: FulfillmentContract | None = None
    completion: CompletionCheckResult | None = None
    artifact_records: list[ArtifactRecord] = field(default_factory=list)


@dataclass
class ReportResult:
    final_answer: str
    execution_tree: str
    summary: str


@dataclass
class NexusResult:
    final_answer: str
    execution_tree: str
    validation_issues: list[str]
    log_path: str