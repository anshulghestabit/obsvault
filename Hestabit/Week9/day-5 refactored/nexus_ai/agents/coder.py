from __future__ import annotations

from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import (
    choose_output_path_from_query,
    ensure_safe_output_path,
    extract_code_block_or_raw,
    infer_deliverable_mode,
    parse_json,
    request_wants_file_output,
)
from nexus_ai.models import WorkerInput, WorkerOutput
from tools.code_executor import run_python_code
from tools.db_agent import csv_columns, csv_schema, preview_csv
from tools.file_agent import write_text_file
from utils.day3_helpers import infer_language_from_path


class CoderAgent(NexusBaseAgent):
    async def _generate_code_only(self, query: str, output_path: str, memory_context: str) -> str:
        language = infer_language_from_path(output_path) if output_path else "python"
        system_prompt = (
            "You are the Coder in NEXUS AI. "
            "Return only one complete runnable code file. "
            "Do not include markdown fences. "
            "Do not include prose."
        )
        user_prompt = (
            f"Task:\n{query}\n\n"
            f"Target output path:\n{output_path}\n\n"
            f"Language:\n{language}\n\n"
            f"Memory context:\n{memory_context}"
        )
        raw = await self._llm_text(system_prompt, user_prompt)
        return extract_code_block_or_raw(raw)

    async def _repair_code_only(
        self,
        query: str,
        output_path: str,
        memory_context: str,
        bad_code: str,
        traceback_text: str,
    ) -> str:
        language = infer_language_from_path(output_path) if output_path else "python"
        system_prompt = (
            "You are the Coder revising code after a failed execution check. "
            "Return only corrected runnable code. "
            "No markdown fences. No prose."
        )
        user_prompt = (
            f"Original task:\n{query}\n\n"
            f"Language:\n{language}\n\n"
            f"Previous code:\n{bad_code}\n\n"
            f"Execution failure:\n{traceback_text}\n\n"
            f"Memory context:\n{memory_context}"
        )
        raw = await self._llm_text(system_prompt, user_prompt)
        return extract_code_block_or_raw(raw)

    async def _run_code_task(self, message: WorkerInput) -> WorkerOutput:
        output_path = message.output_path or str(Path("output/generated_code.py").resolve())
        output_path = ensure_safe_output_path(output_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        code = await self._generate_code_only(message.original_query, output_path, message.memory_context)

        save_result = parse_json(write_text_file(output_path, code))
        resolved_output = ensure_safe_output_path(save_result.get("path", output_path))

        execution_log = "No execution check performed."
        passed = True
        suffix = Path(resolved_output).suffix.lower()

        if suffix == ".py":
            execution_log = run_python_code(
                f'''
import py_compile
py_compile.compile(r"{resolved_output}", doraise=True)
print("Python syntax check passed.")

import subprocess, sys
result = subprocess.run(
    [sys.executable, r"{resolved_output}"],
    capture_output=True,
    text=True,
    timeout=5
)
print("returncode:", result.returncode)
print("stdout:", result.stdout.strip())
print("stderr:", result.stderr.strip())
'''
            )
            parsed = parse_json(execution_log)
            passed = parsed.get("returncode", 1) == 0 and "Traceback" not in str(parsed)

            self._logger.add(
                "coder",
                "code_execution_result",
                {
                    "saved_path": resolved_output,
                    "returncode": parsed.get("returncode"),
                    "stdout": str(parsed.get("stdout", ""))[:1000],
                    "stderr": str(parsed.get("stderr", ""))[:1000],
                },
            )

            if not passed:
                repaired = await self._repair_code_only(
                    message.original_query,
                    resolved_output,
                    message.memory_context,
                    code,
                    str(parsed.get("stderr", execution_log)),
                )
                write_text_file(resolved_output, repaired)
                code = repaired

                execution_log = run_python_code(
                    f'''
import py_compile
py_compile.compile(r"{resolved_output}", doraise=True)
print("Python syntax check passed after repair.")
'''
                )
                reparsed = parse_json(execution_log)
                passed = reparsed.get("returncode", 1) == 0 and "Traceback" not in str(reparsed)

        return WorkerOutput(
            step_id=message.step.step_id,
            owner="coder",
            title=message.step.title,
            result=f"Generated code saved to: {resolved_output}\nExecution status: {'PASS' if passed else 'FAIL'}",
            artifacts={
                "mode": "code_generation",
                "saved_path": resolved_output,
                "code": code,
                "execution_log": execution_log,
                "execution_passed": passed,
            },
            confidence=0.9 if passed else 0.45,
            tool_calls=["write_text_file", "run_python_code"],
            artifacts_created=[resolved_output],
        )

    async def _run_csv_analysis_task(self, message: WorkerInput) -> WorkerOutput:
        target_file = message.target_file
        if not target_file or not Path(target_file).exists():
            return WorkerOutput(
                step_id=message.step.step_id,
                owner="coder",
                title=message.step.title,
                result="No valid target dataset was found.",
                artifacts={"mode": "csv_analysis", "execution_passed": False},
                status="failed",
                confidence=0.1,
                retry_hint="A valid dataset path is required.",
            )

        file_context = (
            f"CSV path:\n{target_file}\n\n"
            f"Columns:\n{csv_columns(target_file)}\n\n"
            f"Schema:\n{csv_schema(target_file)}\n\n"
            f"Preview:\n{preview_csv(target_file, limit=8)}"
        )

        system_prompt = (
            "You are the Coder in NEXUS AI. "
            "Write Python code that analyzes the exact dataset referenced by the user. "
            "Use only the provided file path and real columns. "
            "Print only JSON with keys: answer, supporting_metrics, insights, risks, recommendations. "
            "Do not include markdown fences."
        )
        user_prompt = (
            f"Original query:\n{message.original_query}\n\n"
            f"Assigned step:\n{message.step.instruction}\n\n"
            f"File context:\n{file_context}\n\n"
            f"Memory context:\n{message.memory_context}"
        )

        generated = await self._llm_text(system_prompt, user_prompt)
        generated = extract_code_block_or_raw(generated)

        execution_payload = f"""
import json
import pandas as pd

{generated}
"""
        execution_log = run_python_code(execution_payload)
        parsed = parse_json(execution_log)

        self._logger.add(
            "coder",
            "csv_execution_result",
            {
                "target_file": target_file,
                "returncode": parsed.get("returncode"),
                "stdout": str(parsed.get("stdout", ""))[:1000],
                "stderr": str(parsed.get("stderr", ""))[:1000],
            },
        )

        if parsed.get("returncode", 1) != 0:
            return WorkerOutput(
                step_id=message.step.step_id,
                owner="coder",
                title=message.step.title,
                result="Dataset analysis execution failed.",
                artifacts={
                    "mode": "csv_analysis",
                    "target_file": target_file,
                    "generated_code": generated,
                    "execution_log": execution_log,
                    "execution_passed": False,
                },
                status="failed",
                confidence=0.2,
                tool_calls=["csv_columns", "csv_schema", "preview_csv", "run_python_code"],
                grounding_sources=[target_file],
                retry_hint="Regenerate the data-analysis code using the real schema and preview.",
            )

        stdout = parsed.get("stdout", "")
        metrics = parse_json(stdout)
        answer = metrics.get("answer", stdout)

        return WorkerOutput(
            step_id=message.step.step_id,
            owner="coder",
            title=message.step.title,
            result=str(answer),
            artifacts={
                "mode": "csv_analysis",
                "target_file": target_file,
                "generated_code": generated,
                "execution_log": execution_log,
                "execution_passed": True,
                "metrics": metrics,
            },
            confidence=0.9,
            tool_calls=["csv_columns", "csv_schema", "preview_csv", "run_python_code"],
            grounding_sources=[target_file],
        )

    async def _run_document_task(self, message: WorkerInput) -> WorkerOutput:
        resolved_output = message.output_path or choose_output_path_from_query(message.original_query)
        wants_file = request_wants_file_output(message.original_query) or bool(resolved_output)

        if wants_file and not resolved_output:
            resolved_output = str(Path("output/generated_document.md").resolve())

        if resolved_output:
            resolved_output = ensure_safe_output_path(resolved_output)
            suffix = Path(resolved_output).suffix.lower()
            if suffix not in {".md", ".txt"}:
                resolved_output = ensure_safe_output_path(str(Path(resolved_output).with_suffix(".md")))
            Path(resolved_output).parent.mkdir(parents=True, exist_ok=True)

        system_prompt = (
            "You are the Coder in NEXUS AI. "
            "Produce a deep, structured, implementation-oriented document in markdown. "
            "Do not output source code unless the task explicitly asks for code. "
            "Do not start with imports or code blocks. "
            "Use headings and a human-readable structure. "
            "Include concrete implementation detail, design choices, flow, tradeoffs, validation ideas, and next steps where relevant. "
            "Return only the final markdown document body with no code fences."
        )
        user_prompt = (
            f"Original query:\n{message.original_query}\n\n"
            f"Assigned step:\n{message.step.instruction}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Expected output:\n{message.step.expected_output}\n\n"
            f"Success checks:\n{message.step.success_checks}\n\n"
            f"Target output path:\n{resolved_output}\n\n"
            f"Memory context:\n{message.memory_context}"
        )

        generated = await self._llm_text(system_prompt, user_prompt)
        body = extract_code_block_or_raw(generated).strip()

        # Guard against accidental code dump for document tasks.
        code_markers = ["import ", "def ", "class ", "from ", "if __name__", "print("]
        if any(body.lower().startswith(marker) for marker in code_markers):
            body = (
                "# Deliverable\n\n"
                "The previous generation resembled code rather than a proper document. "
                "This task requires a structured markdown deliverable. "
                "Please review and regenerate if validator flags semantic incompleteness.\n\n"
                "## Raw Generation Snapshot\n\n"
                f"{body}"
            )

        saved_path = ""
        saved_ok = False

        if wants_file and resolved_output:
            save_result = parse_json(write_text_file(resolved_output, body))
            saved_path = ensure_safe_output_path(save_result.get("path", resolved_output))
            saved_ok = Path(saved_path).exists() and Path(saved_path).stat().st_size > 0

        result_text = body
        if saved_ok:
            result_text += f"\n\nSaved document: {saved_path}"

        return WorkerOutput(
            step_id=message.step.step_id,
            owner="coder",
            title=message.step.title,
            result=result_text,
            artifacts={
                "mode": "document",
                "document_saved_path": saved_path,
                "saved_path": saved_path,
                "execution_passed": True if not wants_file else saved_ok,
                "file_exists": saved_ok if wants_file else False,
            },
            confidence=0.86 if body else 0.4,
            tool_calls=["write_text_file"] if wants_file else [],
            artifacts_created=[saved_path] if saved_path else [],
        )

    @message_handler
    async def handle_input(self, message: WorkerInput, ctx: MessageContext) -> WorkerOutput:
        self._logger.add(
            "coder",
            "start",
            {
                "step_id": message.step.step_id,
                "title": message.step.title,
                "task_type": message.task_type,
                "target_file": message.target_file,
                "output_path": message.output_path,
            },
        )

        deliverable_mode = infer_deliverable_mode(message.task_type, message.original_query, message.output_path)

        if deliverable_mode == "code":
            result = await self._run_code_task(message)
        elif message.task_type == "data":
            result = await self._run_csv_analysis_task(message)
        else:
            result = await self._run_document_task(message)

        self._logger.add(
            "coder",
            "finish",
            {
                "step_id": message.step.step_id,
                "result_preview": result.result[:600],
                "artifacts_preview": {
                    k: v for k, v in result.artifacts.items() if k not in {"code", "generated_code"}
                },
            },
        )
        return result