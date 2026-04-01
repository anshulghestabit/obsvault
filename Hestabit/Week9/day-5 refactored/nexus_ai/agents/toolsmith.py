from __future__ import annotations

import re
from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import ensure_safe_output_path, extract_code_block_or_raw, parse_json
from nexus_ai.models import ToolBuildInput, ToolBuildResult
from tools.code_executor import run_python_code
from tools.file_agent import write_text_file


class ToolsmithAgent(NexusBaseAgent):
    def _sanitize_tool_name(self, raw: str) -> str:
        raw = raw.lower().strip()
        raw = re.sub(r"[^a-z0-9_]+", "_", raw)
        raw = re.sub(r"_+", "_", raw).strip("_")
        return (raw or "generated_tool")[:40]

    @message_handler
    async def handle_input(self, message: ToolBuildInput, ctx: MessageContext) -> ToolBuildResult:
        self._logger.add(
            "toolsmith",
            "start",
            {
                "task_type": message.task_type,
                "missing_capability": message.missing_capability,
            },
        )

        system_prompt = (
            "You are the Toolsmith in NEXUS AI. "
            "Create a very small, safe, generic Python helper module for the missing capability. "
            "Return JSON only with keys: tool_name, purpose, import_hint, code. "
            "The code must be a self-contained Python module with one or two focused helper functions only. "
            "Do not write unethical code. "
            "Do not use network access. "
            "Do not modify unrelated files."
        )
        user_prompt = (
            f"Original query:\n{message.query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Missing capability:\n{message.missing_capability}\n\n"
            f"Fulfillment contract:\n{message.contract}\n\n"
            "The helper tool should be generic and reusable inside the current task run."
        )

        data = await self._llm_json(system_prompt, user_prompt)
        tool_name = self._sanitize_tool_name(str(data.get("tool_name", "generated_tool")))
        purpose = str(data.get("purpose", "Run-scoped helper tool"))
        import_hint = str(data.get("import_hint", f"from generated_tools.{tool_name} import main"))
        code = extract_code_block_or_raw(str(data.get("code", "")))

        if not code.strip():
            result = ToolBuildResult(
                built=False,
                tool_name=tool_name,
                file_path="",
                purpose=purpose,
                import_hint=import_hint,
                smoke_test_passed=False,
                error="Toolsmith did not produce valid code.",
            )
            self._logger.add("toolsmith", "finish", result.__dict__)
            return result

        output_dir = Path(message.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = ensure_safe_output_path(str(output_dir / f"{tool_name}.py"))
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        write_text_file(file_path, code)

        smoke_test = run_python_code(
            f"""
import py_compile
py_compile.compile(r"{file_path}", doraise=True)
print("toolsmith_smoke_test_ok")
"""
        )
        parsed = parse_json(smoke_test)
        smoke_ok = parsed.get("returncode", 1) == 0 and "Traceback" not in str(parsed)

        result = ToolBuildResult(
            built=smoke_ok,
            tool_name=tool_name,
            file_path=file_path,
            purpose=purpose,
            import_hint=import_hint,
            smoke_test_passed=smoke_ok,
            error="" if smoke_ok else str(parsed),
        )

        self._logger.add("toolsmith", "finish", result.__dict__)
        return result