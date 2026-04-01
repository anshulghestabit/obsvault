from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_core.models import SystemMessage, UserMessage

from models.day3_messages import CodeResult, DBInspection
from utils.day3_helpers import infer_language_from_path, parse_json, truncate_text
from tools.file_agent import write_text_file


WORKSPACE_DIR = Path("data").resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def run_python_code(code: str) -> str:
    """Run Python code."""
    code = textwrap.dedent(code).strip()
    if not code:
        return json.dumps({"error": "No code provided."}, indent=2)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=WORKSPACE_DIR) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            [sys.executable, str(temp_path)],
            capture_output=True,
            text=True,
            timeout=45,
            cwd=WORKSPACE_DIR,
        )
        return json.dumps(
            {
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "file": str(temp_path),
            },
            indent=2,
        )
    except subprocess.TimeoutExpired:
        return json.dumps(
            {
                "returncode": -1,
                "stdout": "",
                "stderr": "Python execution timed out after 45 seconds.",
                "file": str(temp_path),
            },
            indent=2,
        )


def run_shell_command(command: str) -> str:
    """Run a shell command."""
    command = command.strip()
    if not command:
        return json.dumps({"error": "No command provided."}, indent=2)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20,
            cwd=WORKSPACE_DIR,
        )
        return json.dumps(
            {
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "cwd": str(WORKSPACE_DIR),
            },
            indent=2,
        )
    except subprocess.TimeoutExpired:
        return json.dumps(
            {
                "returncode": -1,
                "stdout": "",
                "stderr": "Shell command timed out after 20 seconds.",
                "cwd": str(WORKSPACE_DIR),
            },
            indent=2,
        )


class CodeAgent(RoutedAgent):
    def __init__(self, name: str, model_client: Any, debug_mode: bool = False) -> None:
        super().__init__(name)
        self._model_client = model_client
        self._debug_mode = debug_mode

    def _debug(self, text: str) -> None:
        if self._debug_mode:
            print(text)

    async def _llm_text(self, system_prompt: str, user_prompt: str, max_chars: int = 10000) -> str:
        result = await self._model_client.create(
            [
                SystemMessage(content=system_prompt),
                UserMessage(content=truncate_text(user_prompt, max_chars), source=self.id.type),
            ]
        )
        return str(result.content).strip()

    async def _generate_analysis_code(
        self,
        query: str,
        file_type: str,
        file_path: str,
        columns: list[str],
        preview: list[dict[str, Any]],
        db_path: str,
        table_name: str,
        requested_items: int,
    ) -> str:
        if file_type == "csv":
            source_hint = f'Load the dataset from CSV path: r"{file_path}" using pandas.'
        else:
            source_hint = (
                f'Load the dataset from SQLite DB path: r"{db_path}", '
                f'read table "{table_name}" into a pandas DataFrame.'
            )

        system_prompt = (
            "You are a data analysis coding agent. "
            "Write Python code only. "
            "The code must answer the user's exact question using the available dataset. "
            "Use only columns that actually exist. "
            "Do not invent columns. "
            "Print only valid JSON with this shape: "
            '{"answer":"...", "supporting_metrics": {...}, "insights":[...]} '
            "Do not include markdown fences."
        )

        user_prompt = (
            f"User query: {query}\n\n"
            f"Dataset type: {file_type}\n"
            f"{source_hint}\n\n"
            f"Available columns: {columns}\n\n"
            f"Preview rows:\n{json.dumps(preview, indent=2)}\n\n"
            f"If the user asked for N insights, try to return {requested_items} when reasonable. "
            "If the query is more specific than generic insights, answer that specific question first.\n\n"
            "Write complete runnable Python code now."
        )

        raw = await self._llm_text(system_prompt, user_prompt)
        code = raw.strip()

        if code.startswith("```"):
            code = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", code)
            code = re.sub(r"\n?```$", "", code).strip()

        return code

    async def _generate_code(self, query: str, output_path: str) -> str:
        language = infer_language_from_path(output_path) if output_path else "python"

        system_prompt = (
            "You are a coding agent. "
            "Generate correct, runnable code only. "
            "Return only the code, with no markdown fences and no explanation."
        )
        user_prompt = (
            f"Task: {query}\n"
            f"Target language: {language}\n"
            f"Output file path: {output_path or 'not provided'}\n"
            "Requirements:\n"
            "- produce complete code\n"
            "- keep it runnable\n"
            "- do not include markdown fences\n"
            "- do not include explanation before or after the code"
        )

        raw = await self._llm_text(system_prompt, user_prompt)
        code = raw.strip()

        if code.startswith("```"):
            code = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", code)
            code = re.sub(r"\n?```$", "", code).strip()

        return code

    @message_handler
    async def handle_db_inspection(self, message: DBInspection, ctx: MessageContext) -> CodeResult:
        self._debug("[code_agent] started")

        if message.intent == "code_generation":
            output_path = message.output_path or "output/generated_code.py"
            code = await self._generate_code(message.query, output_path)

            save_result = parse_json(write_text_file(output_path, code))
            resolved_output = save_result.get("path", output_path)
            execution_log = "No execution check performed."

            suffix = Path(output_path).suffix.lower()
            if suffix == ".py":
                execution_log = run_python_code(
                    f'''
import py_compile
py_compile.compile(r"{str(Path(resolved_output).resolve())}", doraise=True)
print("Python syntax check passed.")

import subprocess, sys
result = subprocess.run(
    [sys.executable, r"{str(Path(resolved_output).resolve())}"],
    capture_output=True,
    text=True,
    timeout=5
)
print("=== RUNTIME CHECK ===")
print("returncode:", result.returncode)
print("stdout:", result.stdout.strip())
print("stderr:", result.stderr.strip())
'''
                )

            self._debug("[code_agent] finished")
            return CodeResult(
                final_answer=(
                    f"Code generated and saved.\n"
                    f"Output path: {resolved_output}\n"
                    f"Language: {infer_language_from_path(output_path)}"
                ),
                raw_metrics={
                    "saved_path": resolved_output,
                    "language": infer_language_from_path(output_path),
                },
                execution_log=execution_log,
            )

        if not message.file_path or not Path(message.file_path).exists():
            return CodeResult(
                final_answer="No valid file was available for analysis.",
                raw_metrics={},
                execution_log="No code executed.",
            )

        if message.file_type not in {"csv", "sqlite"}:
            inspect_log = run_shell_command(f'file "{message.file_path}"')
            return CodeResult(
                final_answer=f"Structured analysis is not supported for this file type.\n\n{inspect_log}",
                raw_metrics={},
                execution_log=inspect_log,
            )

        generated_code = await self._generate_analysis_code(
            query=message.query,
            file_type=message.file_type,
            file_path=message.file_path,
            columns=message.columns,
            preview=message.preview,
            db_path=message.db_path,
            table_name=message.table_name,
            requested_items=message.requested_items,
        )

        if message.file_type == "csv":
            execution_payload = f"""
import pandas as pd
import json

{generated_code}
"""
        else:
            execution_payload = f"""
import sqlite3
import pandas as pd
import json

{generated_code}
"""

        execution_log = run_python_code(execution_payload)
        execution = parse_json(execution_log)

        if execution.get("returncode") != 0:
            return CodeResult(
                final_answer="Code execution failed during analysis.",
                raw_metrics={},
                execution_log=execution_log,
            )

        stdout = str(execution.get("stdout", "")).strip()
        metrics = parse_json(stdout)

        answer = metrics.get("answer")
        if not answer:
            answer = stdout if stdout else "Analysis completed, but no structured answer was produced."

        self._debug("[code_agent] finished")
        return CodeResult(
            final_answer=str(answer),
            raw_metrics=metrics,
            execution_log=execution_log,
        )