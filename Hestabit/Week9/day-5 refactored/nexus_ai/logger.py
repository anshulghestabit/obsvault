from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class NexusLogger:
    def __init__(self, log_dir: str, debug_mode: bool = False) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.events: list[dict[str, Any]] = []
        self.debug_mode = debug_mode

    def add(self, agent: str, event: str, payload: dict[str, Any]) -> None:
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "agent": agent,
            "event": event,
            "payload": payload,
        }
        self.events.append(record)

        if self.debug_mode:
            preview = json.dumps(payload, ensure_ascii=False, default=str)
            if len(preview) > 700:
                preview = preview[:700] + " ...[truncated]"
            print(f"[{record['ts']}] [{agent}] {event} -> {preview}")

    def flush(self, task_name: str = "nexus_run") -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in task_name[:40])
        path = self.log_dir / f"{ts}_{safe_name}.json"
        path.write_text(json.dumps(self.events, indent=2, default=str), encoding="utf-8")
        return str(path.resolve())