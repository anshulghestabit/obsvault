

===== FILE: clients/local_hf_client.py =====

```python
from dataclasses import dataclass
from typing import Sequence

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass
class LocalCreateResult:
    content: str


class LocalHFChatClient:
    def __init__(
        self,
        model_path: str,
        max_new_tokens: int = 180,
    ) -> None:
        self.model_path = model_path
        self.max_new_tokens = max_new_tokens

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
        )

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _messages_to_prompt(self, messages: Sequence[object]) -> str:
        system_blocks = []
        conversation_blocks = []

        for msg in messages:
            content = getattr(msg, "content", "")
            source = getattr(msg, "source", "unknown")
            class_name = msg.__class__.__name__.lower()

            if "system" in class_name:
                system_blocks.append(str(content).strip())
            elif "assistant" in class_name:
                conversation_blocks.append(f"ASSISTANT ({source}):\n{str(content).strip()}")
            else:
                conversation_blocks.append(f"USER ({source}):\n{str(content).strip()}")

        system_text = "\n\n".join(system_blocks).strip()
        conversation_text = "\n\n".join(conversation_blocks).strip()

        prompt = (
            "You must follow the system instructions exactly.\n\n"
            f"SYSTEM INSTRUCTIONS:\n{system_text}\n\n"
            f"CONVERSATION:\n{conversation_text}\n\n"
            "TASK:\n"
            "Write only the next assistant response.\n"
            "Do not create a multi-turn conversation.\n"
            "Do not add USER, ASSISTANT, Chatbot, or Research Agent labels.\n"
            "Do not continue beyond one response.\n\n"
            "ASSISTANT RESPONSE:\n"
        )
        return prompt

    async def create(self, messages: Sequence[object], cancellation_token=None) -> LocalCreateResult:
        prompt = self._messages_to_prompt(messages)

        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )

        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        if decoded.startswith(prompt):
            decoded = decoded[len(prompt):]

        text = decoded.strip()

        stop_markers = [
            "\nUSER",
            "\nASSISTANT",
            "\nChatbot",
            "\nResearch Agent",
            "\nSummarizer Agent",
            "\nAnswer Agent",
        ]
        for marker in stop_markers:
            if marker in text:
                text = text.split(marker)[0].strip()

        return LocalCreateResult(content=text)

    async def close(self) -> None:
        pass
```


===== FILE: clients/openrouter_client.py =====

```python
from dataclasses import dataclass
from typing import Sequence

import requests


@dataclass
class OpenRouterCreateResult:
    content: str


class OpenRouterChatClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        app_url: str = "http://localhost",
        app_title: str = "week9-day1",
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.app_url = app_url
        self.app_title = app_title
        self.timeout = timeout

    def _messages_to_openrouter(self, messages: Sequence[object]) -> list[dict]:
        converted = []

        for msg in messages:
            content = getattr(msg, "content", "")
            class_name = msg.__class__.__name__.lower()

            if "system" in class_name:
                role = "system"
            elif "assistant" in class_name:
                role = "assistant"
            else:
                role = "user"

            converted.append(
                {
                    "role": role,
                    "content": str(content),
                }
            )

        return converted

    async def create(self, messages: Sequence[object], cancellation_token=None) -> OpenRouterCreateResult:
        payload = {
            "model": self.model,
            "messages": self._messages_to_openrouter(messages),
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.app_url,
                "X-OpenRouter-Title": self.app_title,
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return OpenRouterCreateResult(content=content.strip())

    async def close(self) -> None:
        pass
```


===== FILE: llm/api_llm.py =====

```python
import os
import requests
from dotenv import load_dotenv
from config import API_MODEL

load_dotenv()

# --- Model Selection Logic ---
# OpenRouter API Key and URL (Commented)
API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"

# Groq API Key and URL
# API_KEY = os.getenv("GROQ_API_KEY")
# URL = "https://api.groq.com/openai/v1/chat/completions"

import time

def generate_api(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 1 # Groq is faster but still manage rate limits
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    combined_prompt = f"### System Instructions:\n{system_prompt}\n\n### User Prompt:\n{user_prompt}"

    payload = {
        "model": API_MODEL,
        "messages": [
            {"role": "user", "content": combined_prompt}
        ],
        "temperature": 0.7
    }

    for attempt in range(max_retries):
        try:
            # Pacing
            time.sleep(retry_delay)
            
            response = requests.post(URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 429:
                print(f"[API] Rate limited (429). Retrying in {retry_delay*5}s...")
                time.sleep(retry_delay * 5)
                continue
                
            if response.status_code != 200:
                raise Exception(f"API returned error {response.status_code}: {response.text}")

            data = response.json()
            if "choices" not in data:
                raise KeyError(f"Unexpected API response format: {data}")

            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"[API] Error: {e}. Retrying...")
            time.sleep(2)
```


===== FILE: llm/autogen_client.py =====

```python
from typing import Sequence, Any, List, Optional
import asyncio
import json
import re
from autogen_core.models import (
    ChatCompletionClient,
    ModelInfo,
    RequestUsage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    CreateResult,
    LLMMessage,
)
from autogen_core import FunctionCall
from llm.router import generate

class CustomRouterClient(ChatCompletionClient):
    """
    An enhanced AutoGen Model Client that supports 'Function calling without API'
    by injecting tool definitions into the prompt and parsing tool calls from text.
    """
    def __init__(self, **kwargs):
        self._model_info = ModelInfo(
            vision=False, 
            function_calling=True, # We signal TRUE so AutoGen passes tools to us
            json_output=False, 
            family="unknown"
        )
        self.usage = RequestUsage(prompt_tokens=0, completion_tokens=0)

    @property
    def capabilities(self):
        return self._model_info
        
    @property
    def model_info(self):
        return self._model_info

    async def create(self, messages: Sequence[LLMMessage], tools: Optional[Sequence[Any]] = None, **kwargs) -> CreateResult:
        sys_msg = ""
        user_msg = ""
        
        # 1. Handle Tools Injection (Function calling without API)
        if tools:
            tool_desc = "\n### AVAILABLE TOOLS\n"
            for tool in tools:
                # Handle dictionary format (OpenAI-style)
                if isinstance(tool, dict):
                    f_part = tool.get("function", tool)
                    name = f_part.get("name", "unknown")
                    desc = f_part.get("description", "")
                    params = f_part.get("parameters", {})
                else:
                    # Handle AutoGen Tool objects or raw functions
                    name = getattr(tool, "name", None) or getattr(tool, "__name__", "unknown")
                    desc = getattr(tool, "description", None) or getattr(tool, "__doc__", "")
                    # AutoGen tools have json_schema or parameters
                    params = getattr(tool, "parameters", {})
                    if not params and hasattr(tool, "json_schema"):
                        params = tool.json_schema

                tool_desc += f"Tool Name: {name}\nDescription: {desc}\nParameters JSON: {json.dumps(params)}\n\n"
            
            tool_desc += """
### TOOL CALLING PROTOCOL
To execute a tool, you MUST use the following format:
CALL: tool_name(parameter_name='value', ...)

Example:
CALL: read_file(path='data.csv')

DO NOT use XML tags. DO NOT use any other format.
"""
            sys_msg += tool_desc
            # logger.debug(f"Injected tools: {[getattr(t, 'name', 'unnamed') for t in tools]}")

        for m in messages:
            if isinstance(m, SystemMessage):
                sys_msg += m.content + "\n"
            elif isinstance(m, UserMessage):
                content = m.content if isinstance(m.content, str) else str(m.content)
                user_msg += f"USER: {content}\n"
            elif isinstance(m, AssistantMessage):
                user_msg += f"ASSISTANT: {m.content}\n"
            
            # Identify by class name to avoid import issues if names vary
            msg_type = type(m).__name__
            if msg_type == "ToolCallRequestEvent":
                for call in getattr(m, "content", []):
                    user_msg += f"ASSISTANT CALLS TOOL: {getattr(call, 'name', 'unknown')}({getattr(call, 'arguments', '')})\n"
            elif msg_type == "ToolCallExecutionEvent":
                for result in getattr(m, "content", []):
                    content = getattr(result, "content", "")
                    user_msg += f"TOOL RESULT: {content}\n"

        # 2. Generate Completion
        # print(f"DEBUG: SYS: {sys_msg[:200]}...")
        # print(f"DEBUG: USER: {user_msg[:200]}...")
        loop = asyncio.get_event_loop()
        res_text = await loop.run_in_executor(None, generate, sys_msg.strip(), user_msg.strip())
        if res_text is None:
            res_text = ""
        # print(f"DEBUG: LLM RES: {res_text}")

        # 3. Parse Tool Calls (Function calling without API)
        tool_calls = []
        
        # Pattern 1: CALL: tool_name(args)
        match_call = re.search(r"CALL:\s*(\w+)\((.*)\)", res_text, re.DOTALL)
        
        # Pattern 2: ```tool_call\n tool_name(args)
        match_md = re.search(r"```(?:tool_call|tool_code|python)?\s*(\w+)\((.*)\)\s*```", res_text, re.DOTALL)
        
        # Pattern 3: <function=name>... (Legacy/Alt)
        match_xml = re.search(r"<function=(\w+)>(.*?)</function>", res_text, re.DOTALL)

        if match_call:
            tool_name = match_call.group(1)
            args_str = match_call.group(2).strip()
        elif match_md:
            tool_name = match_md.group(1)
            args_str = match_md.group(2).strip()
        elif match_xml:
            tool_name = match_xml.group(1)
            args_str = match_xml.group(2).strip()
        else:
            return CreateResult(
                finish_reason="stop",
                content=res_text,
                usage=self.usage,
                cached=False
            )
            
        # Simple Argument Extraction
        args = {}
        # Try to match key='value', key="value", or key=value
        # or even JSON-like {"key": "value"}
        if args_str.startswith("{") and args_str.endswith("}"):
            try:
                args = json.loads(args_str)
            except: pass
        
        if not args:
            # Use a state-machine parser instead of regex to correctly handle
            # nested quotes, multiline code, and multiple arguments
            args = self._parse_tool_args(args_str)

        if not args:
            # Try to match <parameter name='key'>value</parameter>
            xml_params = re.findall(r"<parameter\s+name=['\"](\w+)['\"]>(.*?)</parameter>", args_str, re.DOTALL)
            if xml_params:
                for k, v in xml_params:
                    args[k.strip()] = v.strip()
            
            # Alternative XML: <key>value</key>
            if not args:
                xml_params2 = re.findall(r"<(\w+)>(.*?)</\1>", args_str, re.DOTALL)
                if xml_params2:
                    for k, v in xml_params2:
                        args[k.strip()] = v.strip()

        tool_calls.append(FunctionCall(
            id=f"call_{int(asyncio.get_event_loop().time())}",
            arguments=json.dumps(args),
            name=tool_name
        ))

        if tool_calls:
            return CreateResult(
                finish_reason="function_calls",
                content=tool_calls,
                usage=self.usage,
                cached=False
            )
        else:
            return CreateResult(
                finish_reason="stop",
                content=res_text,
                usage=self.usage,
                cached=False
            )
        
    def _parse_tool_args(self, args_str: str) -> dict:
        """
        State-machine parser for tool arguments like:
            code='def foo():\n    pass', language='python'
        Correctly handles nested quotes, multiline strings, and escaped characters.
        """
        args = {}
        i = 0
        n = len(args_str)

        while i < n:
            # Skip whitespace and commas
            while i < n and args_str[i] in (' ', '\t', '\n', ','):
                i += 1
            if i >= n:
                break

            # Read key
            key_start = i
            while i < n and args_str[i] not in ('=', ' ', '\t'):
                i += 1
            key = args_str[key_start:i].strip()
            if not key:
                break

            # Skip to '='
            while i < n and args_str[i] != '=':
                i += 1
            i += 1  # skip '='

            # Skip whitespace after '='
            while i < n and args_str[i] in (' ', '\t'):
                i += 1
            if i >= n:
                break

            # Determine quote character(s)
            if args_str[i] in ('"', "'"):
                quote_char = args_str[i]
                # Check for triple quotes
                if i + 2 < n and args_str[i:i+3] == quote_char * 3:
                    delimiter = quote_char * 3
                    i += 3
                else:
                    delimiter = quote_char
                    i += 1

                # Read value until matching closing delimiter
                val_start = i
                while i < n:
                    if args_str[i] == '\\' and i + 1 < n:
                        i += 2  # skip escaped char
                        continue
                    if args_str[i:i+len(delimiter)] == delimiter:
                        break
                    i += 1
                value = args_str[val_start:i]
                i += len(delimiter)  # skip closing delimiter

                # Unescape common sequences
                value = value.replace("\\n", "\n").replace("\\t", "\t")
                value = value.replace('\\"', '"').replace("\\'", "'")
            elif args_str[i] == '[':
                # Read list until matching ']'
                val_start = i
                depth = 0
                while i < n:
                    if args_str[i] == '[': depth += 1
                    elif args_str[i] == ']': depth -= 1
                    i += 1
                    if depth == 0: break
                value = args_str[val_start:i]
                # Try to load as JSON to get a real list object if possible
                try:
                    value = json.loads(value.replace("'", '"'))
                except: pass
            elif args_str[i] == '{':
                # Read dict until matching '}'
                val_start = i
                depth = 0
                while i < n:
                    if args_str[i] == '{': depth += 1
                    elif args_str[i] == '}': depth -= 1
                    i += 1
                    if depth == 0: break
                value = args_str[val_start:i]
                # Try to load as JSON
                try:
                    value = json.loads(value.replace("'", '"'))
                except: pass
            else:
                # Unquoted value — read until comma or end
                val_start = i
                while i < n and args_str[i] != ',':
                    i += 1
                value = args_str[val_start:i].strip()

            if key:
                args[key] = value

        return args

    async def create_stream(self, messages, **kwargs):
        res = await self.create(messages, **kwargs)
        yield str(res.content)
        
    def actual_usage(self) -> RequestUsage:
        return self.usage
    
    def total_usage(self) -> RequestUsage:
        return self.usage

    def count_tokens(self, messages, **kwargs) -> int:
        return 0

    def remaining_tokens(self, messages, **kwargs) -> int:
        return 0
        
    async def close(self):
        pass
```


===== FILE: llm/local_llm.py =====

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from config import LOCAL_MODEL

_tokenizer = None
_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def _load_model():
    global _tokenizer, _model
    if _model is None or _tokenizer is None:
        print(f"Loading local model to {_device}...")
        _tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL)
        
        load_kwargs = {
            "low_cpu_mem_usage": True,
            "torch_dtype": torch.float16 if _device == "cuda" else torch.float32,
        }
        
        _model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL, **load_kwargs).to(_device)
        print("Local model loaded")
    return _tokenizer, _model


def generate_local(system_prompt, user_prompt):
    tokenizer, model = _load_model()

    # TinyLlama Chat Template format
    prompt = f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_prompt}</s>\n<|assistant|>\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(_device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode only the NEW tokens
    generated_ids = outputs[0][inputs.input_ids.shape[-1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)

    return response.strip()
```


===== FILE: llm/router.py =====

```python
from config import MODEL_PROVIDER


def generate(system_prompt, user_prompt):

    if MODEL_PROVIDER == "local":
        from llm.local_llm import generate_local
        return generate_local(system_prompt, user_prompt)

    elif MODEL_PROVIDER == "api":
        from llm.api_llm import generate_api
        return generate_api(system_prompt, user_prompt)

    else:
        raise ValueError("Invalid model provider")
```


===== FILE: memory/manager.py =====

```python
import sqlite3
import os
from datetime import datetime
from memory.session_memory import SessionMemory
from memory.vector_store import VectorStore
from llm.router import generate

DB_PATH = "memory/long_term.db"

class MemoryManager:
    def __init__(self):
        self.session = SessionMemory()
        self.vector_store = VectorStore()
        self._init_db()

    def _init_db(self):
        os.makedirs("memory", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                role TEXT,
                content TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def store_interaction(self, role, content):
        """Conversation stored in both session and SQLite."""
        # 1. Session Memory
        self.session.add_message(role, content)
        
        # 2. Long-term SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (role, content))
        conn.commit()
        conn.close()

    def get_augmented_context(self, query):
        """Search memory -> Fetch similar context."""
        relevant_facts = self.vector_store.search(query, top_k=2)
        if not relevant_facts:
            return ""
        
        context = "\n### RECALLED MEMORY\n"
        for fact in relevant_facts:
            context += f"- {fact}\n"
        return context

    def summarize_and_store_fact(self):
        """Important facts summarized and stored in FAISS."""
        history_text = self.session.get_full_text()
        if not history_text:
            return
            
        summary_prompt = f"""Summarize the following conversation into 1-2 key facts that are worth remembering for the long term. 
If there's nothing important, reply with 'NONE'.

Conversation:
{history_text}

Summary fact:"""
        
        try:
            summary = generate("You are a memory compressor.", summary_prompt)
            if summary and summary.strip().upper() != "NONE":
                self.vector_store.add_fact(summary.strip())
                print(f"  [MEMORY] New fact stored: {summary.strip()}")
        except Exception as e:
            print(f"  [MEMORY WARN] Failed to summarize: {e}")

if __name__ == "__main__":
    mm = MemoryManager()
    mm.store_interaction("user", "My name is Abhay.")
    mm.summarize_and_store_fact()
    print("Augmented Context for 'who am I?':", mm.get_augmented_context("who am I?"))
```


===== FILE: memory/session_memory.py =====

```python
from __future__ import annotations

import sqlite3
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque


@dataclass
class ConversationTurn:
    role: str
    content: str


@dataclass
class FactRecord:
    fact: str
    category: str
    source: str


class SessionMemory:
    def __init__(self, db_path: str = "memory/long_term.db", max_turns: int = 10) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_turns = max_turns
        self.turns: Deque[ConversationTurn] = deque(maxlen=max_turns)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()
        conn.close()

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append(ConversationTurn(role=role, content=content))

        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO conversations (role, content) VALUES (?, ?)",
            (role, content),
        )
        conn.commit()
        conn.close()

    def get_recent_context(self) -> list[ConversationTurn]:
        return list(self.turns)

    def format_recent_context(self) -> str:
        if not self.turns:
            return "No recent session context."

        lines = []
        for turn in self.turns:
            lines.append(f"{turn.role.upper()}: {turn.content}")
        return "\n".join(lines)

    def extract_important_facts(self, text: str) -> list[FactRecord]:
        facts: list[FactRecord] = []
        lowered = text.lower()

        preference_patterns = [
            ("preference", "prefers"),
            ("preference", "likes"),
            ("preference", "wants"),
            ("preference", "needs"),
            ("constraint", "must"),
            ("constraint", "should"),
            ("identity", "i am"),
            ("identity", "my name is"),
            ("project", "project"),
            ("task", "working on"),
        ]

        for category, marker in preference_patterns:
            if marker in lowered:
                facts.append(FactRecord(fact=text.strip(), category=category, source="session"))
                break

        if not facts and len(text.split()) <= 20:
            facts.append(FactRecord(fact=text.strip(), category="note", source="session"))

        deduped = []
        seen = set()
        for fact in facts:
            key = (fact.fact, fact.category)
            if key not in seen:
                seen.add(key)
                deduped.append(fact)

        return deduped

    def store_facts(self, facts: list[FactRecord]) -> None:
        if not facts:
            return

        conn = self._connect()
        cur = conn.cursor()

        for fact in facts:
            cur.execute(
                "INSERT INTO facts (fact, category, source) VALUES (?, ?, ?)",
                (fact.fact, fact.category, fact.source),
            )

        conn.commit()
        conn.close()

    def search_facts(self, query: str, limit: int = 5) -> list[FactRecord]:
        tokens = [token.strip() for token in query.lower().split() if len(token.strip()) > 2]
        if not tokens:
            return []

        conn = self._connect()
        cur = conn.cursor()

        clauses = " OR ".join(["LOWER(fact) LIKE ?"] * len(tokens))
        values = [f"%{token}%" for token in tokens]
        sql = f"""
            SELECT fact, category, source
            FROM facts
            WHERE {clauses}
            ORDER BY id DESC
            LIMIT ?
        """
        cur.execute(sql, (*values, limit))
        rows = cur.fetchall()
        conn.close()

        return [FactRecord(fact=row[0], category=row[1], source=row[2]) for row in rows]

    def format_fact_results(self, facts: list[FactRecord]) -> str:
        if not facts:
            return "No matching long-term facts."

        lines = []
        for idx, fact in enumerate(facts, start=1):
            lines.append(f"{idx}. [{fact.category}] {fact.fact}")
        return "\n".join(lines)
```


===== FILE: memory/vector_store.py =====

```python
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer


@dataclass
class VectorMemoryItem:
    text: str
    metadata: dict


class FaissVectorStore:
    def __init__(
        self,
        index_path: str = "memory/vector.index",
        metadata_path: str = "memory/vector_metadata.pkl",
        dim: int = 1024,
    ) -> None:
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self.dim = dim
        self.vectorizer = HashingVectorizer(
            n_features=self.dim,
            alternate_sign=False,
            norm="l2",
        )

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = faiss.IndexFlatIP(self.dim)

        if self.metadata_path.exists():
            with open(self.metadata_path, "rb") as f:
                self.items: list[VectorMemoryItem] = pickle.load(f)
        else:
            self.items = []

    def _embed(self, texts: list[str]) -> np.ndarray:
        matrix = self.vectorizer.transform(texts)
        dense = matrix.toarray().astype("float32")
        return dense

    def add_text(self, text: str, metadata: dict | None = None) -> None:
        metadata = metadata or {}
        vector = self._embed([text])
        self.index.add(vector)
        self.items.append(VectorMemoryItem(text=text, metadata=metadata))
        self.save()

    def search(self, query: str, k: int = 3) -> list[dict]:
        if not self.items or self.index.ntotal == 0:
            return []

        query_vector = self._embed([query])
        scores, indices = self.index.search(query_vector, min(k, len(self.items)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            item = self.items[idx]
            results.append(
                {
                    "text": item.text,
                    "metadata": item.metadata,
                    "score": float(score),
                }
            )
        return results

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.items, f)

    def clear(self) -> None:
        self.index = faiss.IndexFlatIP(self.dim)
        self.items = []
        self.save()

    def format_search_results(self, results: list[dict]) -> str:
        if not results:
            return "No similar vector memories found."

        lines = []
        for idx, item in enumerate(results, start=1):
            text = item["text"]
            meta = json.dumps(item["metadata"], ensure_ascii=False)
            score = round(item["score"], 4)
            lines.append(f"{idx}. score={score} | {text} | metadata={meta}")
        return "\n".join(lines)
```


===== FILE: models/day3_messages.py =====

```python
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
```


===== FILE: nexus_ai/__init__.py =====

```python

```


===== FILE: nexus_ai/agents/__init__.py =====

```python

```


===== FILE: nexus_ai/agents/analyst.py =====

```python
from __future__ import annotations

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import WorkerInput, WorkerOutput


class AnalystAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: WorkerInput, ctx: MessageContext) -> WorkerOutput:
        self._logger.add(
            "analyst",
            "start",
            {
                "step_id": message.step.step_id,
                "title": message.step.title,
                "task_type": message.task_type,
                "target_file": message.target_file,
            },
        )

        system_prompt = (
            "You are the Analyst in NEXUS AI. "
            "Focus on tradeoffs, business impact, feasibility, prioritization, risk, and decision quality. "
            "If the query involves a dataset, convert grounded findings into actions, strategy, and implications. "
            "Do not write code."
        )

        user_prompt = (
            f"Original query:\n{message.original_query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Memory context:\n{message.memory_context}\n\n"
            f"Target file:\n{message.target_file}\n\n"
            f"Assigned step:\n{message.step.instruction}"
        )

        text = await self._llm_text(system_prompt, user_prompt)

        result = WorkerOutput(
            step_id=message.step.step_id,
            owner="analyst",
            title=message.step.title,
            result=text,
            artifacts={
                "execution_passed": True,
            },
        )

        self._logger.add(
            "analyst",
            "finish",
            {
                "step_id": message.step.step_id,
                "result_preview": text[:500],
            },
        )
        return result
```


===== FILE: nexus_ai/agents/base.py =====

```python
from __future__ import annotations

import json
import re
from typing import Any

from autogen_core import RoutedAgent
from autogen_core.models import SystemMessage, UserMessage

from nexus_ai.logger import NexusLogger
from utils.day3_helpers import truncate_text


class NexusBaseAgent(RoutedAgent):
    def __init__(
        self,
        name: str,
        model_client: Any,
        nexus_logger: NexusLogger,
        debug_mode: bool = False,
    ) -> None:
        super().__init__(name)
        self._model_client = model_client
        self._logger = nexus_logger
        self._debug_mode = debug_mode

    def _debug(self, text: str) -> None:
        if self._debug_mode:
            print(text)

    async def _llm_text(self, system_prompt: str, user_prompt: str, max_chars: int = 12000) -> str:
        result = await self._model_client.create(
            [
                SystemMessage(content=system_prompt),
                UserMessage(content=truncate_text(user_prompt, max_chars), source=self.id.type),
            ]
        )
        return str(result.content).strip()

    async def _llm_json(self, system_prompt: str, user_prompt: str, max_chars: int = 12000) -> dict:
        raw = await self._llm_text(system_prompt, user_prompt, max_chars=max_chars)
        cleaned = raw.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return {}
```


===== FILE: nexus_ai/agents/coder.py =====

```python
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
```


===== FILE: nexus_ai/agents/completion_checker.py =====

```python
from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import (
    choose_output_path_from_query,
    extract_count_requirements,
    extract_expected_sections_from_query,
    infer_deliverable_mode,
    infer_depth_threshold,
)
from nexus_ai.models import (
    ArtifactRecord,
    ArtifactRequirement,
    CompletionCheckInput,
    CompletionCheckResult,
    ContractRequest,
    FulfillmentContract,
)


class CompletionCheckerAgent(NexusBaseAgent):
    def _infer_semantic_requirements(self, query: str) -> list[str]:
        q = query.lower()
        semantic: list[str] = []

        if "pipeline" in q:
            semantic.extend(["stages", "flow", "components"])

        if "rag" in q or "retrieval augmented generation" in q:
            semantic.extend(
                [
                    "ingestion",
                    "chunking",
                    "embedding",
                    "indexing",
                    "retrieval",
                    "augmentation",
                    "generation",
                ]
            )

        if "architecture" in q:
            semantic.extend(["components", "data flow", "deployment", "tradeoffs"])

        if "training module" in q or "curriculum" in q:
            semantic.extend(["week", "day", "topics", "exercise", "deliverables"])

        if "strategy" in q or "roadmap" in q or "plan" in q:
            semantic.extend(["phases", "risks", "milestones", "execution"])

        cleaned: list[str] = []
        for item in semantic:
            if item not in cleaned:
                cleaned.append(item)
        return cleaned

    def _heuristic_contract(self, query: str, task_type: str, output_path: str) -> FulfillmentContract:
        resolved_output = output_path or choose_output_path_from_query(query)
        deliverable_mode = infer_deliverable_mode(task_type, query, resolved_output)
        expected_sections = extract_expected_sections_from_query(query)
        expected_sections.extend(self._infer_semantic_requirements(query))

        deduped_sections: list[str] = []
        for item in expected_sections:
            if item not in deduped_sections:
                deduped_sections.append(item)

        count_requirements = extract_count_requirements(query)
        requested_folder = Path(resolved_output).parent.name if resolved_output else ""
        must_create_new_folder = "new folder" in query.lower() and bool(requested_folder)

        artifact_requirements: list[ArtifactRequirement] = []
        if resolved_output:
            artifact_requirements.append(
                ArtifactRequirement(
                    name="primary_output",
                    path_hint=resolved_output,
                    format=Path(resolved_output).suffix.lower(),
                    must_exist=True,
                    description="Primary deliverable requested by the user.",
                )
            )

        structural_requirements = []
        if deduped_sections:
            structural_requirements.append("include explicitly requested sections and semantic components")
        if count_requirements:
            structural_requirements.append("satisfy quantified requirements from the prompt")
        if must_create_new_folder:
            structural_requirements.append("honor the user-requested new folder location")

        return FulfillmentContract(
            task_summary=query[:300],
            deliverable_mode=deliverable_mode,
            requested_output_path=resolved_output,
            requested_folder=requested_folder,
            must_create_new_folder=must_create_new_folder,
            structural_requirements=structural_requirements,
            count_requirements=count_requirements,
            expected_sections=deduped_sections,
            min_depth_chars=infer_depth_threshold(task_type, query),
            artifact_requirements=artifact_requirements,
            success_criteria=[
                "directly answers the task",
                "is sufficiently detailed for the scope",
                "saves the requested artifact when requested",
                "covers the required semantic components of the task",
            ],
        )

    @message_handler
    async def handle_contract_request(self, message: ContractRequest, ctx: MessageContext) -> FulfillmentContract:
        self._logger.add(
            "completion_checker",
            "contract_start",
            {
                "query": message.query,
                "task_type": message.task_type,
                "output_path": message.output_path,
            },
        )

        heuristic = self._heuristic_contract(message.query, message.task_type, message.output_path)

        system_prompt = (
            "You are the Completion Checker in NEXUS AI. "
            "Extract a generic fulfillment contract from the user task. "
            "Return JSON only with keys: "
            "task_summary, deliverable_mode, structural_requirements, count_requirements, expected_sections, min_depth_chars, success_criteria, must_create_new_folder. "
            "Be strict about semantic completeness. "
            "Do not assume a specific domain unless the user asks for one."
        )
        user_prompt = (
            f"Query:\n{message.query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Resolved output path:\n{message.output_path}\n\n"
            f"Heuristic contract:\n{asdict(heuristic)}"
        )

        data = await self._llm_json(system_prompt, user_prompt)

        contract = FulfillmentContract(
            task_summary=str(data.get("task_summary", heuristic.task_summary)),
            deliverable_mode=str(data.get("deliverable_mode", heuristic.deliverable_mode)),
            requested_output_path=heuristic.requested_output_path,
            requested_folder=heuristic.requested_folder,
            must_create_new_folder=bool(data.get("must_create_new_folder", heuristic.must_create_new_folder)),
            structural_requirements=list(data.get("structural_requirements", heuristic.structural_requirements)),
            count_requirements=dict(data.get("count_requirements", heuristic.count_requirements)),
            expected_sections=list(data.get("expected_sections", heuristic.expected_sections)),
            min_depth_chars=int(data.get("min_depth_chars", heuristic.min_depth_chars)),
            artifact_requirements=heuristic.artifact_requirements,
            success_criteria=list(data.get("success_criteria", heuristic.success_criteria)),
        )

        self._logger.add(
            "completion_checker",
            "contract_finish",
            {"contract": asdict(contract)},
        )
        return contract

    def _collect_artifact_records(self, worker_outputs, contract: FulfillmentContract) -> list[ArtifactRecord]:
        records: dict[str, ArtifactRecord] = {}

        def add_record(name: str, path_str: str, created_by: str) -> None:
            if not path_str:
                return
            path = Path(path_str)
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            records[str(path.resolve())] = ArtifactRecord(
                name=name,
                path=str(path.resolve()),
                exists=exists,
                size_bytes=size,
                created_by=created_by,
                status="verified" if exists and size > 0 else "missing",
            )

        for output in worker_outputs:
            for key in ["saved_path", "document_saved_path", "final_saved_path", "file_path", "tool_file_path"]:
                value = output.artifacts.get(key)
                if isinstance(value, str) and value.strip():
                    add_record(key, value, output.owner)

            for value in output.artifacts_created:
                if isinstance(value, str) and value.strip():
                    add_record("artifact_created", value, output.owner)

        if contract.requested_output_path:
            add_record("requested_output", contract.requested_output_path, "requested")

        return list(records.values())

    def _count_in_draft(self, unit: str, draft: str, artifact_records: list[ArtifactRecord]) -> int:
        lower = draft.lower()

        if unit == "week":
            return len(set(re.findall(r"\bweek\s+\d+\b", lower)))
        if unit == "day":
            return len(set(re.findall(r"\bday\s+\d+\b", lower)))
        if unit == "file":
            return sum(1 for record in artifact_records if record.exists)
        if unit == "section":
            return len(re.findall(r"^#+\s+.+$", draft, flags=re.MULTILINE))
        if unit == "agent":
            return len(set(re.findall(r"\bagent\b", lower)))
        return 0

    def _section_satisfied(self, section: str, draft: str) -> bool:
        section = section.lower().strip()
        lower = draft.lower()

        if section in lower:
            return True

        tokens = [t for t in re.findall(r"[a-zA-Z]{4,}", section)]
        if not tokens:
            return False

        # More strict than before: require meaningful token match.
        matched = sum(1 for token in tokens if token in lower)
        return matched >= max(1, min(2, len(tokens)))

    @message_handler
    async def handle_completion_check(self, message: CompletionCheckInput, ctx: MessageContext) -> CompletionCheckResult:
        self._logger.add(
            "completion_checker",
            "check_start",
            {
                "query": message.query,
                "task_type": message.task_type,
            },
        )

        contract = message.contract
        artifact_records = self._collect_artifact_records(message.worker_outputs, contract)
        draft = message.draft or ""

        missing_requirements: list[str] = []
        satisfied_requirements: list[str] = []
        task_satisfaction: dict[str, bool] = {}

        if contract.requested_output_path:
            matching = [r for r in artifact_records if Path(r.path).resolve() == Path(contract.requested_output_path).resolve()]
            ok = any(r.exists and r.size_bytes > 0 for r in matching)
            task_satisfaction["requested_output_exists"] = ok
            if ok:
                satisfied_requirements.append("requested output artifact exists")
            else:
                missing_requirements.append("requested output artifact was not created or is empty")

        if contract.must_create_new_folder and contract.requested_folder:
            ok = any(Path(r.path).parent.name == contract.requested_folder and r.exists for r in artifact_records)
            task_satisfaction["requested_folder_honored"] = ok
            if ok:
                satisfied_requirements.append("requested folder location was honored")
            else:
                missing_requirements.append("requested folder location was not honored")

        depth_ok = len(draft.strip()) >= contract.min_depth_chars
        task_satisfaction["depth_ok"] = depth_ok
        if depth_ok:
            satisfied_requirements.append("response depth is sufficient")
        else:
            missing_requirements.append(
                f"response is too shallow for the task scope (need about {contract.min_depth_chars}+ characters of substantive content)"
            )

        for section in contract.expected_sections:
            ok = self._section_satisfied(section, draft)
            task_satisfaction[f"section::{section}"] = ok
            if ok:
                satisfied_requirements.append(f"section covered: {section}")
            else:
                missing_requirements.append(f"missing requested section or semantic component: {section}")

        for unit, required_count in contract.count_requirements.items():
            actual = self._count_in_draft(unit, draft, artifact_records)
            ok = actual >= required_count
            task_satisfaction[f"count::{unit}"] = ok
            if ok:
                satisfied_requirements.append(f"count satisfied for {unit}: {actual}/{required_count}")
            else:
                missing_requirements.append(f"count requirement not satisfied for {unit}: found {actual}, expected {required_count}")

        fulfilled = len(missing_requirements) == 0
        summary = "Fulfillment contract satisfied." if fulfilled else "Fulfillment contract has unmet requirements."

        result = CompletionCheckResult(
            fulfilled=fulfilled,
            missing_requirements=missing_requirements,
            satisfied_requirements=satisfied_requirements,
            artifact_records=artifact_records,
            task_satisfaction=task_satisfaction,
            summary=summary,
        )

        self._logger.add(
            "completion_checker",
            "check_finish",
            {
                "fulfilled": result.fulfilled,
                "missing_requirements": result.missing_requirements,
                "artifact_records": [asdict(r) for r in result.artifact_records],
            },
        )
        return result
```


===== FILE: nexus_ai/agents/critic.py =====

```python
from __future__ import annotations

import json
from dataclasses import asdict

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import CritiqueInput, CritiqueResult


class CriticAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: CritiqueInput, ctx: MessageContext) -> CritiqueResult:
        self._logger.add(
            "critic",
            "start",
            {
                "task_type": message.task_type,
                "worker_outputs": len(message.worker_outputs),
            },
        )

        system_prompt = (
            "You are the Critic in NEXUS AI. "
            "Find weak reasoning, missing steps, risky assumptions, execution failures, and grounding gaps. "
            "Return JSON only: {\"critique\":\"...\",\"risks\":[\"...\", ...]}"
        )
        user_prompt = (
            f"Query:\n{message.query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Plan:\n{json.dumps([asdict(s) for s in message.plan], indent=2)}\n\n"
            f"Worker outputs:\n{json.dumps([asdict(o) for o in message.worker_outputs], indent=2)}"
        )

        raw = await self._llm_text(system_prompt, user_prompt)

        try:
            data = json.loads(raw)
            result = CritiqueResult(
                critique=data.get("critique", ""),
                risks=data.get("risks", []),
            )
        except Exception:
            risks = []
            for output in message.worker_outputs:
                if output.artifacts.get("execution_passed") is False:
                    risks.append(f"{output.owner} step {output.step_id} had execution failure.")
            if not risks:
                risks.append("Possible missing details or weak grounding.")
            result = CritiqueResult(
                critique="Fallback critique: review grounding, completeness, and execution truth.",
                risks=risks,
            )

        self._logger.add(
            "critic",
            "finish",
            {
                "critique_preview": result.critique[:400],
                "risks": result.risks,
            },
        )
        return result
```


===== FILE: nexus_ai/agents/optimizer.py =====

```python
from __future__ import annotations

from dataclasses import asdict

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import OptimizationInput, OptimizationResult


class OptimizerAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: OptimizationInput, ctx: MessageContext) -> OptimizationResult:
        self._logger.add(
            "optimizer",
            "start",
            {
                "task_type": message.task_type,
                "worker_outputs": len(message.worker_outputs),
            },
        )

        if any(o.artifacts.get("mode") == "code_generation" for o in message.worker_outputs):
            coder = next((o for o in message.worker_outputs if o.owner == "coder"), None)
            improved = coder.result if coder else "\n\n".join(o.result for o in message.worker_outputs)
            result = OptimizationResult(
                improved_draft=improved,
                improvements=["Preserved execution-validated implementation output."],
            )
        else:
            system_prompt = (
                "You are the Optimizer in NEXUS AI. "
                "Rewrite the worker outputs into a deeper, cleaner, more complete final draft. "
                "Do not just concatenate. "
                "Use the critique to close gaps, improve structure, increase depth, and produce a more implementation-ready answer. "
                "Return JSON only with keys: improved_draft, improvements."
            )
            user_prompt = (
                f"Query:\n{message.query}\n\n"
                f"Task type:\n{message.task_type}\n\n"
                f"Worker outputs:\n{[asdict(o) for o in message.worker_outputs]}\n\n"
                f"Critique:\n{message.critique}"
            )

            data = await self._llm_json(system_prompt, user_prompt)
            improved_draft = str(data.get("improved_draft", "")).strip()
            improvements = list(data.get("improvements", []))

            if not improved_draft:
                merged = ["# Synthesized Response", ""]
                for output in message.worker_outputs:
                    merged.append(f"## {output.owner.capitalize()} — {output.title}")
                    merged.append(output.result.strip())
                    merged.append("")
                if message.critique:
                    merged.append("## Critique To Address")
                    merged.append(message.critique.strip())
                improved_draft = "\n".join(merged).strip()
                improvements = improvements or ["Used structured synthesis fallback instead of raw concatenation."]

            result = OptimizationResult(
                improved_draft=improved_draft,
                improvements=improvements,
            )

        self._logger.add(
            "optimizer",
            "finish",
            {
                "draft_preview": result.improved_draft[:600],
                "improvements": result.improvements,
            },
        )
        return result
```


===== FILE: nexus_ai/agents/orchestrator.py =====

```python
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from autogen_core import AgentId, MessageContext, message_handler

from memory.session_memory import SessionMemory
from memory.vector_store import FaissVectorStore
from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import (
    build_memory_context,
    choose_output_path_from_query,
    ensure_safe_output_path,
    request_wants_file_output,
)
from nexus_ai.logger import NexusLogger
from nexus_ai.models import (
    CompletionCheckInput,
    ContractRequest,
    CritiqueInput,
    NexusResult,
    NexusTask,
    OptimizationInput,
    ReportInput,
    ValidationInput,
    WorkerInput,
    WorkerOutput,
)
from tools.file_agent import write_text_file


def _print_agent_banner(agent: str, phase: str, detail: str = "") -> None:
    width = 72
    top = "╔" + "═" * (width - 2) + "╗"
    bot = "╚" + "═" * (width - 2) + "╝"
    body = f"║  [{agent.upper()}]  →  {phase}"
    body = body + " " * (width - len(body) - 1) + "║"
    print(f"\n{top}")
    print(body)
    if detail:
        clipped = str(detail)[: width - 7]
        det_line = f"║     {clipped}"
        det_line = det_line + " " * (width - len(det_line) - 1) + "║"
        print(det_line)
    print(bot)


class OrchestratorAgent(NexusBaseAgent):
    def __init__(
        self,
        name: str,
        model_client,
        nexus_logger: NexusLogger,
        session_memory: SessionMemory,
        vector_store: FaissVectorStore,
        debug_mode: bool = False,
    ) -> None:
        super().__init__(name, model_client, nexus_logger, debug_mode)
        self._session_memory = session_memory
        self._vector_store = vector_store

    def _normalize_issue_text(self, issue) -> str:
        if isinstance(issue, str):
            return issue
        if isinstance(issue, dict):
            if "issue" in issue:
                return str(issue["issue"])
            if "message" in issue:
                return str(issue["message"])
            return json.dumps(issue, ensure_ascii=False)
        if isinstance(issue, list):
            return ", ".join(str(x) for x in issue)
        return str(issue)

    def _normalize_issue_list(self, issues) -> list[str]:
        if not issues:
            return []
        normalized = [self._normalize_issue_text(issue).strip() for issue in issues]
        return [item for item in normalized if item]

    async def _dispatch_step(
        self,
        run_id: str,
        query: str,
        step,
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
        owner_override: str | None = None,
    ) -> WorkerOutput:
        owner = owner_override or step.owner
        target = {
            "researcher": "researcher",
            "coder": "coder",
            "analyst": "analyst",
        }.get(owner, "researcher")

        self._logger.add(
            "orchestrator",
            "dispatch_step",
            {
                "run_id": run_id,
                "step_id": step.step_id,
                "owner": owner,
                "original_owner": step.owner,
                "title": step.title,
                "task_type": task_type,
                "target_file": target_file,
                "output_path": output_path,
                "depends_on": getattr(step, "depends_on", []),
                "can_run_parallel": getattr(step, "can_run_parallel", False),
            },
        )

        return await self.send_message(
            WorkerInput(
                original_query=query,
                step=step,
                memory_context=memory_context,
                task_type=task_type,
                target_file=target_file,
                output_path=output_path,
            ),
            AgentId(target, "default"),
        )

    def _normalize_output(self, item, step) -> WorkerOutput:
        if isinstance(item, Exception):
            self._logger.add(
                "orchestrator",
                "worker_exception",
                {
                    "step_id": step.step_id,
                    "owner": step.owner,
                    "title": step.title,
                    "error": str(item),
                },
            )
            return WorkerOutput(
                step_id=step.step_id,
                owner=step.owner,
                title=step.title,
                result=f"Failure recovered with placeholder: {str(item)}",
                artifacts={"execution_passed": False},
                status="failed",
                confidence=0.1,
                retry_hint=str(item),
            )

        self._logger.add(
            "orchestrator",
            "worker_result_received",
            {
                "step_id": item.step_id,
                "owner": item.owner,
                "title": item.title,
                "status": item.status,
                "result_preview": item.result[:500],
            },
        )
        return item

    async def _run_step_with_fallbacks(
        self,
        run_id: str,
        query: str,
        step,
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
        retry_suffix: str = "",
    ) -> WorkerOutput:
        candidate_owners = [step.owner] + [o for o in getattr(step, "fallback_owners", []) if o != step.owner]
        final_query = query if not retry_suffix else f"{query}\n\nRetry guidance:\n{retry_suffix}"

        for idx, owner in enumerate(candidate_owners):
            try:
                if idx == 0:
                    _print_agent_banner(owner, f"Step {step.step_id} — {step.title}", f"Instruction: {step.instruction[:80]}...")
                else:
                    _print_agent_banner(owner, f"Fallback handoff for Step {step.step_id} — {step.title}", f"Trying alternate owner: {owner}")

                output = await self._dispatch_step(
                    run_id=run_id,
                    query=final_query,
                    step=step,
                    memory_context=memory_context,
                    task_type=task_type,
                    target_file=target_file,
                    output_path=output_path,
                    owner_override=owner,
                )

                if owner != step.owner:
                    output = WorkerOutput(
                        step_id=output.step_id,
                        owner=step.owner,
                        title=output.title,
                        result=output.result,
                        artifacts={**output.artifacts, "handled_by": owner},
                        status=output.status,
                        confidence=output.confidence,
                        tool_calls=output.tool_calls,
                        tool_results=output.tool_results,
                        grounding_sources=output.grounding_sources,
                        artifacts_created=output.artifacts_created,
                        needs_handoff=output.needs_handoff,
                        handoff_target=output.handoff_target,
                        retry_hint=output.retry_hint,
                    )

                if output.artifacts.get("execution_passed") is False and idx < len(candidate_owners) - 1:
                    self._logger.add(
                        "orchestrator",
                        "handoff_triggered",
                        {
                            "run_id": run_id,
                            "step_id": step.step_id,
                            "from_owner": owner,
                            "to_owner": candidate_owners[idx + 1],
                            "reason": "execution_passed=False",
                        },
                    )
                    continue

                return output
            except Exception as exc:
                self._logger.add(
                    "orchestrator",
                    "worker_exception",
                    {
                        "run_id": run_id,
                        "step_id": step.step_id,
                        "owner": owner,
                        "title": step.title,
                        "error": str(exc),
                    },
                )

        return WorkerOutput(
            step_id=step.step_id,
            owner=step.owner,
            title=step.title,
            result="All attempts failed for this step.",
            artifacts={"execution_passed": False},
            status="failed",
            confidence=0.1,
            retry_hint="Fallback owners were exhausted.",
        )

    async def _execute_in_dependency_waves(
        self,
        run_id: str,
        query: str,
        steps: list,
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
    ) -> list[WorkerOutput]:
        pending = {getattr(step, "step_id", idx + 1): step for idx, step in enumerate(steps)}
        completed: dict[int, WorkerOutput] = {}
        outputs: list[WorkerOutput] = []
        wave_number = 0

        while pending:
            ready_steps = [
                step for _, step in pending.items()
                if all(dep in completed for dep in getattr(step, "depends_on", []))
            ]

            if not ready_steps:
                for step_id, step in pending.items():
                    failed = WorkerOutput(
                        step_id=getattr(step, "step_id", step_id),
                        owner=getattr(step, "owner", "unknown"),
                        title=getattr(step, "title", "Untitled"),
                        result="Step could not run because dependencies were unresolved.",
                        artifacts={"execution_passed": False, "deadlock": True},
                        status="failed",
                        confidence=0.1,
                    )
                    completed[getattr(step, "step_id", step_id)] = failed
                    outputs.append(failed)
                break

            wave_number += 1
            self._logger.add(
                "orchestrator",
                "wave_ready",
                {
                    "run_id": run_id,
                    "wave_number": wave_number,
                    "steps": [
                        {
                            "step_id": step.step_id,
                            "owner": step.owner,
                            "title": step.title,
                            "depends_on": step.depends_on,
                            "can_run_parallel": step.can_run_parallel,
                        }
                        for step in ready_steps
                    ],
                },
            )

            tasks = [
                self._run_step_with_fallbacks(
                    run_id=run_id,
                    query=query,
                    step=step,
                    memory_context=memory_context,
                    task_type=task_type,
                    target_file=target_file,
                    output_path=output_path,
                )
                for step in ready_steps
            ]
            raw_outputs = await asyncio.gather(*tasks, return_exceptions=True)

            for step, raw in zip(ready_steps, raw_outputs):
                normalized = self._normalize_output(raw, step)
                completed[getattr(step, "step_id", -1)] = normalized
                outputs.append(normalized)
                pending.pop(getattr(step, "step_id", -1), None)

        outputs.sort(key=lambda x: x.step_id)
        return outputs

    def _find_verified_saved_artifact(self, worker_outputs: list[WorkerOutput]) -> str:
        for output in worker_outputs:
            for key in ["saved_path", "document_saved_path", "final_saved_path", "file_path", "tool_file_path"]:
                path = output.artifacts.get(key)
                if path and Path(path).exists() and Path(path).stat().st_size > 0:
                    return str(Path(path).resolve())
        return ""

    def _persist_text_artifact(self, output_path: str, content: str, step_id: int, title: str) -> WorkerOutput:
        resolved = ensure_safe_output_path(output_path)
        Path(resolved).parent.mkdir(parents=True, exist_ok=True)
        write_text_file(resolved, content)

        exists = Path(resolved).exists() and Path(resolved).stat().st_size > 0

        return WorkerOutput(
            step_id=step_id,
            owner="orchestrator",
            title=title,
            result=f"Persisted artifact: {resolved}" if exists else f"Failed to persist artifact: {resolved}",
            artifacts={
                "mode": "final_document",
                "saved_path": resolved,
                "final_saved_path": resolved,
                "execution_passed": exists,
            },
            confidence=1.0 if exists else 0.1,
            tool_calls=["write_text_file"],
            artifacts_created=[resolved] if exists else [],
        )

    async def _retry_targeted_steps(
        self,
        run_id: str,
        query: str,
        retry_targets: list[str],
        plan_steps: list,
        existing_outputs: list[WorkerOutput],
        memory_context: str,
        task_type: str,
        target_file: str,
        output_path: str,
        issues: list[str],
    ) -> list[WorkerOutput]:
        retry_steps = [step for step in plan_steps if step.owner in retry_targets]
        if not retry_steps:
            retry_steps = plan_steps

        retry_suffix = "\n".join(self._normalize_issue_list(issues)[:10])
        retried_outputs: list[WorkerOutput] = []

        for step in retry_steps:
            retried = await self._run_step_with_fallbacks(
                run_id=run_id,
                query=query,
                step=step,
                memory_context=memory_context,
                task_type=task_type,
                target_file=target_file,
                output_path=output_path,
                retry_suffix=retry_suffix,
            )
            retried_outputs.append(retried)

        outputs_by_step = {o.step_id: o for o in existing_outputs}
        for retried in retried_outputs:
            outputs_by_step[retried.step_id] = retried

        final_outputs = list(outputs_by_step.values())
        final_outputs.sort(key=lambda x: x.step_id)
        return final_outputs

    @message_handler
    async def handle_task(self, message: NexusTask, ctx: MessageContext) -> NexusResult:
        run_id = uuid.uuid4().hex[:12]

        _print_agent_banner(
            "orchestrator",
            "Task received — building memory context & routing to agents",
            f"Run ID: {run_id} | Query: {message.query[:60]}...",
        )
        self._logger.add("orchestrator", "start", {"run_id": run_id, "query": message.query})

        memory_context = build_memory_context(message.query, self._session_memory, self._vector_store)
        self._logger.add(
            "orchestrator",
            "memory_context_built",
            {
                "run_id": run_id,
                "preview": memory_context[:1000],
            },
        )

        _print_agent_banner("planner", "Analysing task and building an execution graph")
        plan = await self.send_message(message, AgentId("planner", "default"))
        raw_output_path = plan.output_path or choose_output_path_from_query(message.query)
        resolved_output_path = ensure_safe_output_path(raw_output_path) if raw_output_path else ""

        contract = await self.send_message(
            ContractRequest(
                query=message.query,
                task_type=plan.task_type,
                output_path=resolved_output_path,
            ),
            AgentId("completion_checker", "default"),
        )

        self._logger.add(
            "orchestrator",
            "plan_received",
            {
                "run_id": run_id,
                "task_type": plan.task_type,
                "target_file": plan.target_file,
                "output_path": resolved_output_path,
                "planning_notes": plan.planning_notes,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "owner": step.owner,
                        "title": step.title,
                        "depends_on": step.depends_on,
                        "can_run_parallel": step.can_run_parallel,
                    }
                    for step in plan.steps
                ],
            },
        )

        worker_outputs = await self._execute_in_dependency_waves(
            run_id=run_id,
            query=message.query,
            steps=plan.steps,
            memory_context=memory_context,
            task_type=plan.task_type,
            target_file=plan.target_file,
            output_path=resolved_output_path,
        )

        _print_agent_banner("critic", "Evaluating worker outputs for risks & gaps")
        critique = await self.send_message(
            CritiqueInput(
                query=message.query,
                task_type=plan.task_type,
                plan=plan.steps,
                worker_outputs=worker_outputs,
            ),
            AgentId("critic", "default"),
        )

        _print_agent_banner("optimizer", "Synthesising an improved draft from all worker outputs")
        optimizer = await self.send_message(
            OptimizationInput(
                query=message.query,
                task_type=plan.task_type,
                worker_outputs=worker_outputs,
                critique=critique.critique,
            ),
            AgentId("optimizer", "default"),
        )

        wants_file_output = request_wants_file_output(message.query)
        verified_saved_path = self._find_verified_saved_artifact(worker_outputs)

        if wants_file_output and not verified_saved_path and contract.requested_output_path:
            worker_outputs.append(
                self._persist_text_artifact(
                    contract.requested_output_path,
                    optimizer.improved_draft,
                    step_id=999,
                    title="Persist optimized draft artifact before validation",
                )
            )

        completion = await self.send_message(
            CompletionCheckInput(
                query=message.query,
                task_type=plan.task_type,
                draft=optimizer.improved_draft,
                worker_outputs=worker_outputs,
                plan=plan.steps,
                contract=contract,
            ),
            AgentId("completion_checker", "default"),
        )

        _print_agent_banner("validator", "Checking draft for correctness, completeness & quality")
        validator = await self.send_message(
            ValidationInput(
                query=message.query,
                task_type=plan.task_type,
                draft=optimizer.improved_draft,
                worker_outputs=worker_outputs,
                plan=plan.steps,
                contract=contract,
                completion=completion,
            ),
            AgentId("validator", "default"),
        )

        normalized_validator_issues = self._normalize_issue_list(validator.issues)

        self._logger.add(
            "orchestrator",
            "validation_result",
            {
                "run_id": run_id,
                "passed": validator.passed,
                "score": validator.score,
                "issues": normalized_validator_issues,
                "retry_targets": validator.retry_targets,
            },
        )

        if validator.needs_retry and validator.retry_targets:
            worker_outputs = await self._retry_targeted_steps(
                run_id=run_id,
                query=message.query,
                retry_targets=validator.retry_targets,
                plan_steps=plan.steps,
                existing_outputs=worker_outputs,
                memory_context=memory_context,
                task_type=plan.task_type,
                target_file=plan.target_file,
                output_path=resolved_output_path,
                issues=normalized_validator_issues,
            )

            optimizer = await self.send_message(
                OptimizationInput(
                    query=message.query,
                    task_type=plan.task_type,
                    worker_outputs=worker_outputs,
                    critique=critique.critique,
                ),
                AgentId("optimizer", "default"),
            )

            if wants_file_output and not self._find_verified_saved_artifact(worker_outputs) and contract.requested_output_path:
                worker_outputs.append(
                    self._persist_text_artifact(
                        contract.requested_output_path,
                        optimizer.improved_draft,
                        step_id=1000,
                        title="Persist optimized draft artifact after retry",
                    )
                )

            completion = await self.send_message(
                CompletionCheckInput(
                    query=message.query,
                    task_type=plan.task_type,
                    draft=optimizer.improved_draft,
                    worker_outputs=worker_outputs,
                    plan=plan.steps,
                    contract=contract,
                ),
                AgentId("completion_checker", "default"),
            )

            validator = await self.send_message(
                ValidationInput(
                    query=message.query,
                    task_type=plan.task_type,
                    draft=optimizer.improved_draft,
                    worker_outputs=worker_outputs,
                    plan=plan.steps,
                    contract=contract,
                    completion=completion,
                ),
                AgentId("validator", "default"),
            )
            normalized_validator_issues = self._normalize_issue_list(validator.issues)

        _print_agent_banner("reporter", "Compiling the final answer and execution tree")
        report = await self.send_message(
            ReportInput(
                query=message.query,
                task_type=plan.task_type,
                plan=plan.steps,
                worker_outputs=worker_outputs,
                critique=critique.critique,
                improvements=optimizer.improvements,
                validated_answer=validator.validated_answer,
                contract=contract,
                completion=completion,
                artifact_records=completion.artifact_records,
            ),
            AgentId("reporter", "default"),
        )

        final_answer = report.final_answer
        final_saved_path = self._find_verified_saved_artifact(worker_outputs)

        if wants_file_output and contract.requested_output_path:
            final_persist = self._persist_text_artifact(
                contract.requested_output_path,
                final_answer,
                step_id=1001,
                title="Persist final report artifact",
            )
            self._logger.add(
                "orchestrator",
                "final_artifact_save_attempt",
                {
                    "run_id": run_id,
                    "requested": True,
                    "output_path": contract.requested_output_path,
                    "saved_ok": final_persist.artifacts.get("execution_passed"),
                    "saved_path": final_persist.artifacts.get("saved_path"),
                },
            )
            if final_persist.artifacts.get("execution_passed"):
                final_saved_path = str(final_persist.artifacts.get("saved_path"))
                if "Saved output file:" not in final_answer:
                    final_answer += f"\n\nSaved output file: {final_saved_path}"

        validation_issues = self._normalize_issue_list(validator.issues)

        if final_saved_path and Path(final_saved_path).exists() and Path(final_saved_path).stat().st_size > 0:
            validation_issues = [
                issue for issue in validation_issues
                if "saved artifact was produced" not in issue.lower()
            ]

        self._session_memory.add_turn("user", message.query)
        self._session_memory.add_turn("assistant", final_answer)
        self._session_memory.store_facts(self._session_memory.extract_important_facts(message.query))
        self._session_memory.store_facts(self._session_memory.extract_important_facts(final_answer))
        self._vector_store.add_text(message.query, {"role": "user", "run_id": run_id})
        self._vector_store.add_text(final_answer, {"role": "assistant", "run_id": run_id})

        self._logger.add(
            "orchestrator",
            "finish",
            {
                "run_id": run_id,
                "saved_path": final_saved_path,
                "validation_issues": validation_issues,
            },
        )
        log_path = self._logger.flush(task_name="nexus_ai")

        return NexusResult(
            final_answer=final_answer,
            execution_tree=report.execution_tree,
            validation_issues=validation_issues,
            log_path=log_path,
        )
```


===== FILE: nexus_ai/agents/planner.py =====

```python
from __future__ import annotations

from dataclasses import asdict

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import choose_output_path_from_query, choose_target_file_from_query, detect_task_type, request_wants_file_output
from nexus_ai.models import NexusTask, PlanResult, PlanStep


class PlannerAgent(NexusBaseAgent):
    def _build_generic_plan(self, query: str, task_type: str, output_path: str) -> list[PlanStep]:
        wants_file = request_wants_file_output(query) or bool(output_path)

        return [
            PlanStep(
                step_id=1,
                title="Clarify scope and success criteria",
                owner="researcher",
                instruction=(
                    f"Clarify the user's true intent, required structure, acceptance criteria, constraints, counts, "
                    f"and artifact expectations for: {query}"
                ),
                expected_output="structured task interpretation",
                success_checks=[
                    "task intent clarified",
                    "constraints identified",
                    "success criteria identified",
                ],
                max_retries=1,
            ),
            PlanStep(
                step_id=2,
                title="Produce the main deliverable",
                owner="coder",
                instruction=(
                    f"Create the main deliverable for: {query}. "
                    f"It must be detailed, implementation-oriented, and satisfy the clarified success criteria."
                ),
                depends_on=[1],
                can_run_parallel=True,
                fallback_owners=["researcher"],
                required_tools=["file_agent"] if wants_file else [],
                expected_output="main deliverable",
                success_checks=[
                    "main deliverable produced",
                    "artifact saved if requested" if wants_file else "usable output produced",
                    "goes beyond shallow summary",
                ],
                max_retries=2,
            ),
            PlanStep(
                step_id=3,
                title="Analyze completeness and practicality",
                owner="analyst",
                instruction=(
                    f"Analyze the deliverable for completeness, depth, tradeoffs, usability, gaps, "
                    f"and practical execution quality for: {query}"
                ),
                depends_on=[1],
                can_run_parallel=True,
                fallback_owners=["researcher"],
                expected_output="quality analysis",
                success_checks=[
                    "gaps identified",
                    "practicality reviewed",
                    "tradeoffs reviewed",
                ],
                max_retries=1,
            ),
        ]

    def _build_deterministic_plan(self, query: str) -> PlanResult:
        task_type = detect_task_type(query)
        target_file = choose_target_file_from_query(query)
        output_path = choose_output_path_from_query(query)

        steps = self._build_generic_plan(query, task_type, output_path)

        return PlanResult(
            steps=steps,
            planning_notes="Generic planner-worker-validator graph derived from task contract, not from domain-specific routing.",
            task_type=task_type,
            target_file=target_file,
            output_path=output_path,
        )

    @message_handler
    async def handle_task(self, message: NexusTask, ctx: MessageContext) -> PlanResult:
        self._logger.add("planner", "start", {"query": message.query})

        result = self._build_deterministic_plan(message.query)

        self._logger.add(
            "planner",
            "finish",
            {
                "task_type": result.task_type,
                "target_file": result.target_file,
                "output_path": result.output_path,
                "steps": [asdict(step) for step in result.steps],
            },
        )
        return result
```


===== FILE: nexus_ai/agents/reporter.py =====

```python
from __future__ import annotations

from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import ReportInput, ReportResult


class ReporterAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: ReportInput, ctx: MessageContext) -> ReportResult:
        self._logger.add(
            "reporter",
            "start",
            {
                "task_type": message.task_type,
                "query": message.query,
            },
        )

        tree_lines = [f"User Query: {message.query}", "└── orchestrator", "    ├── planner"]
        for step in message.plan:
            parallel_note = " [parallel]" if getattr(step, "can_run_parallel", False) else ""
            tree_lines.append(f"    ├── {step.owner} -> {step.title}{parallel_note}")
        tree_lines.append("    ├── critic -> critique worker outputs")
        tree_lines.append("    ├── optimizer -> strengthen draft")
        tree_lines.append("    ├── completion_checker -> compare against fulfillment contract")
        tree_lines.append("    ├── validator -> validate final state")
        tree_lines.append("    └── reporter -> finalize response")

        if message.artifact_records:
            tree_lines.append("")
            tree_lines.append("Artifacts:")
            for artifact in message.artifact_records:
                status = "OK" if artifact.exists else "MISSING"
                tree_lines.append(f"  - {artifact.name}: {artifact.path} [{status}]")

        final_answer = message.validated_answer.strip()

        if message.completion is not None:
            final_answer += "\n\n## Fulfillment Status\n"
            final_answer += f"- Contract satisfied: {'Yes' if message.completion.fulfilled else 'No'}\n"
            if message.completion.satisfied_requirements:
                final_answer += "- Satisfied requirements:\n"
                for item in message.completion.satisfied_requirements[:12]:
                    final_answer += f"  - {item}\n"
            if message.completion.missing_requirements:
                final_answer += "- Remaining gaps:\n"
                for item in message.completion.missing_requirements[:12]:
                    final_answer += f"  - {item}\n"

        if message.artifact_records:
            final_answer += "\n## Artifact Manifest\n"
            for artifact in message.artifact_records:
                size = artifact.size_bytes if artifact.exists else 0
                final_answer += (
                    f"- {artifact.name}: {artifact.path} | exists={artifact.exists} | "
                    f"size={size} | created_by={artifact.created_by}\n"
                )

        code_output = next((o for o in message.worker_outputs if o.artifacts.get("mode") == "code_generation"), None)
        if code_output:
            exec_log = code_output.artifacts.get("execution_log", "")
            saved = code_output.artifacts.get("saved_path", "")
            if saved:
                final_answer += f"\nSaved file: {saved}"
            if exec_log:
                final_answer += f"\n\n## Execution Check\n{exec_log}"

        summary = (
            message.completion.summary
            if message.completion is not None
            else "Reported the validated answer with execution trace."
        )

        result = ReportResult(
            final_answer=final_answer,
            execution_tree="\n".join(tree_lines),
            summary=summary,
        )

        self._logger.add(
            "reporter",
            "finish",
            {"summary_preview": summary[:400]},
        )
        return result
```


===== FILE: nexus_ai/agents/researcher.py =====

```python
from __future__ import annotations

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.models import WorkerInput, WorkerOutput
from tools.db_agent import csv_columns, csv_schema, preview_csv


class ResearcherAgent(NexusBaseAgent):
    @message_handler
    async def handle_input(self, message: WorkerInput, ctx: MessageContext) -> WorkerOutput:
        self._logger.add(
            "researcher",
            "start",
            {
                "step_id": message.step.step_id,
                "title": message.step.title,
                "task_type": message.task_type,
                "target_file": message.target_file,
            },
        )

        file_context = ""
        if message.target_file:
            if message.target_file.lower().endswith(".csv"):
                file_context = (
                    f"Target file: {message.target_file}\n"
                    f"Columns: {csv_columns(message.target_file)}\n\n"
                    f"Schema: {csv_schema(message.target_file)}\n\n"
                    f"Preview: {preview_csv(message.target_file, limit=5)}"
                )
            else:
                file_context = f"Target file: {message.target_file}"

        system_prompt = (
            "You are the Researcher in NEXUS AI. "
            "Provide concise factual, domain, strategic, or requirements context for the assigned step. "
            "Use the file context when available. "
            "Do not write code and do not produce the final answer."
        )

        user_prompt = (
            f"Original query:\n{message.original_query}\n\n"
            f"Task type:\n{message.task_type}\n\n"
            f"Memory context:\n{message.memory_context}\n\n"
            f"File context:\n{file_context}\n\n"
            f"Assigned step:\n{message.step.instruction}"
        )

        text = await self._llm_text(system_prompt, user_prompt)

        result = WorkerOutput(
            step_id=message.step.step_id,
            owner="researcher",
            title=message.step.title,
            result=text,
            artifacts={
                "grounded_file": message.target_file,
                "execution_passed": True,
            },
        )

        self._logger.add(
            "researcher",
            "finish",
            {
                "step_id": message.step.step_id,
                "result_preview": text[:500],
            },
        )
        return result
```


===== FILE: nexus_ai/agents/toolsmith.py =====

```python
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
```


===== FILE: nexus_ai/agents/validator.py =====

```python
from __future__ import annotations

import re
from pathlib import Path

from autogen_core import MessageContext, message_handler

from nexus_ai.agents.base import NexusBaseAgent
from nexus_ai.helpers import infer_deliverable_mode
from nexus_ai.models import ValidationInput, ValidationResult


class ValidatorAgent(NexusBaseAgent):
    def _derive_retry_targets(self, issues: list[str], plan) -> list[str]:
        targets: set[str] = set()
        text = " ".join(issues).lower()

        for issue in issues:
            m = re.search(r"Missing expected worker outputs from: (.+)", issue)
            if m:
                owners = [item.strip() for item in m.group(1).split(",")]
                targets.update(owners)

        if any(k in text for k in ["artifact", "saved file", "output path", "folder", "created"]):
            targets.add("coder")

        if any(k in text for k in ["shallow", "missing requested section", "missing requested section or semantic component", "structure", "depth", "count requirement"]):
            targets.update({"optimizer", "researcher", "coder"})

        if any(k in text for k in ["execution", "syntax", "failed"]):
            targets.add("coder")

        if not targets and plan:
            targets.update(step.owner for step in plan)

        return sorted(targets)

    @message_handler
    async def handle_input(self, message: ValidationInput, ctx: MessageContext) -> ValidationResult:
        self._logger.add(
            "validator",
            "start",
            {
                "task_type": message.task_type,
                "query": message.query,
            },
        )

        issues: list[str] = []
        artifact_checks: dict[str, object] = {}
        grounding_checks: dict[str, object] = {}
        completeness_checks: dict[str, object] = {}

        produced_owners = {o.owner for o in message.worker_outputs}
        expected_owners = {step.owner for step in message.plan} if message.plan else set()

        missing_owners = sorted(expected_owners - produced_owners)
        if missing_owners:
            issues.append(f"Missing expected worker outputs from: {', '.join(missing_owners)}")

        for output in message.worker_outputs:
            if output.artifacts.get("execution_passed") is False:
                issues.append(f"{output.owner} step '{output.title}' failed execution.")
            if output.status == "failed":
                issues.append(f"{output.owner} step '{output.title}' returned failed status.")
            if not output.result or len(output.result.strip()) < 20:
                issues.append(f"{output.owner} step '{output.title}' produced too little usable output.")

        contract = message.contract
        completion = message.completion

        if contract is not None:
            artifact_checks["requested_output_path"] = contract.requested_output_path
            artifact_checks["deliverable_mode"] = contract.deliverable_mode
            completeness_checks["min_depth_chars"] = contract.min_depth_chars

            if contract.deliverable_mode == "code":
                coder = next((o for o in message.worker_outputs if o.owner == "coder"), None)
                if coder is None:
                    issues.append("Coder output missing for code-oriented task.")
                else:
                    saved_path = coder.artifacts.get("saved_path")
                    artifact_checks["code_saved_path"] = saved_path
                    if not saved_path or not Path(saved_path).exists():
                        issues.append("Generated or revised code file was not saved.")
                    if coder.artifacts.get("execution_passed") is not True:
                        issues.append("Generated or revised code did not pass execution validation.")

            # Critical check: document requests should not pass if coder emitted code-like content.
            if contract.deliverable_mode == "document":
                coder = next((o for o in message.worker_outputs if o.owner == "coder"), None)
                if coder:
                    text = coder.result.strip().lower()
                    code_markers = ["import ", "def ", "class ", "from ", "if __name__", "print("]
                    if any(marker in text for marker in code_markers) and not text.lstrip().startswith("#"):
                        issues.append("Document-style task appears to contain code-oriented output instead of a proper structured document.")

        if completion is not None:
            artifact_checks["artifact_records"] = [
                {"path": a.path, "exists": a.exists, "status": a.status}
                for a in completion.artifact_records
            ]
            completeness_checks["task_satisfaction"] = completion.task_satisfaction
            if not completion.fulfilled:
                issues.extend(completion.missing_requirements)

        deliverable_mode = infer_deliverable_mode(
            message.task_type,
            message.query,
            contract.requested_output_path if contract else "",
        )

        if deliverable_mode == "document" and len(message.draft.strip()) < 200:
            issues.append("Document-style answer is too short to be reliable.")

        retry_targets = self._derive_retry_targets(sorted(set(issues)), message.plan)
        score = max(0.0, 1.0 - (0.10 * len(set(issues))))

        if issues:
            result = ValidationResult(
                passed=False,
                issues=sorted(set(issues)),
                validated_answer=message.draft,
                score=score,
                needs_retry=True,
                retry_targets=retry_targets,
                artifact_checks=artifact_checks,
                grounding_checks=grounding_checks,
                completeness_checks=completeness_checks,
            )
        else:
            system_prompt = (
                "You are the Validator in NEXUS AI. "
                "Check the answer for clarity, directness, correctness, completeness, and obvious mistakes. "
                "Return JSON only with keys: passed, issues, validated_answer, score, needs_retry, retry_targets."
            )
            user_prompt = (
                f"Query:\n{message.query}\n\n"
                f"Task type:\n{message.task_type}\n\n"
                f"Draft answer:\n{message.draft}\n\n"
                f"Completion summary:\n{completion.summary if completion else 'N/A'}"
            )
            data = await self._llm_json(system_prompt, user_prompt)

            result = ValidationResult(
                passed=bool(data.get("passed", True)),
                issues=list(data.get("issues", [])),
                validated_answer=str(data.get("validated_answer", message.draft)),
                score=float(data.get("score", 0.92)),
                needs_retry=bool(data.get("needs_retry", False)),
                retry_targets=list(data.get("retry_targets", [])),
                artifact_checks=artifact_checks,
                grounding_checks=grounding_checks,
                completeness_checks=completeness_checks,
            )

        self._logger.add(
            "validator",
            "finish",
            {
                "passed": result.passed,
                "score": result.score,
                "issues": result.issues,
                "retry_targets": result.retry_targets,
            },
        )
        return result
```


===== FILE: nexus_ai/config.py =====

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


@dataclass
class NexusSettings:
    model_provider: str
    api_provider: str
    local_model: str
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_model: str
    groq_api_key: str
    groq_base_url: str
    groq_model: str
    debug_mode: bool
    log_dir: str
    max_plan_steps: int
    parallel_workers: int
    session_db_path: str
    vector_index_path: str
    vector_metadata_path: str


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_nexus_settings() -> NexusSettings:
    return NexusSettings(
        model_provider=os.getenv("MODEL_PROVIDER", "local").strip().lower(),
        api_provider=os.getenv("API_PROVIDER", "groq").strip().lower(),
        local_model=os.getenv("LOCAL_MODEL", "models/tinyllama").strip(),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip(),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free").strip(),
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip(),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
        debug_mode=_to_bool(os.getenv("DEBUG_MODE", "false")),
        log_dir=os.getenv("NEXUS_LOG_DIR", "logs"),
        max_plan_steps=int(os.getenv("NEXUS_MAX_PLAN_STEPS", "6")),
        parallel_workers=int(os.getenv("NEXUS_PARALLEL_WORKERS", "3")),
        session_db_path=os.getenv("NEXUS_SESSION_DB", "memory/long_term.db"),
        vector_index_path=os.getenv("NEXUS_VECTOR_INDEX", "memory/vector.index"),
        vector_metadata_path=os.getenv("NEXUS_VECTOR_META", "memory/vector_metadata.pkl"),
    )
```


===== FILE: nexus_ai/helpers.py =====

```python
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from memory.session_memory import SessionMemory
from memory.vector_store import FaissVectorStore
from tools.file_agent import list_files


_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def parse_json(text: str) -> dict:
    if isinstance(text, dict):
        return text
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def parse_list_files() -> list[str]:
    try:
        data = json.loads(list_files("."))
        return data.get("files", [])
    except Exception:
        return []


def normalize_path_text(path: str) -> str:
    return path.replace("\\", "/").strip().lower()


def _normalize_query_for_paths(query: str) -> str:
    q = query.replace("\\", "/")
    q = q.replace("ouput/", "output/")
    q = q.replace("otput/", "output/")
    q = q.replace("outpt/", "output/")
    return q


def _slugify(text: str, max_len: int = 64) -> str:
    text = text.lower()
    text = re.sub(r"[<>]", " ", text)
    text = re.sub(
        r"\b(save|saved|saving|in|to|at|as|write|the|whole|file|output|markdown|report|document|folder|newly|created|naming)\b",
        " ",
        text,
    )
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return (text or "nexus_output")[:max_len].rstrip("_")


def _trim_segment(segment: str, max_len: int) -> str:
    if len(segment) <= max_len:
        return segment
    stem, suffix = os.path.splitext(segment)
    if suffix:
        allowed = max(8, max_len - len(suffix))
        return stem[:allowed] + suffix
    return segment[:max_len]


def ensure_safe_output_path(path_str: str) -> str:
    path = Path(path_str)
    cleaned_parts: list[str] = []

    for idx, part in enumerate(path.parts):
        if idx == 0 and part in {"/", "\\"}:
            cleaned_parts.append(part)
            continue
        max_len = 72 if idx == len(path.parts) - 1 else 40
        cleaned_parts.append(_trim_segment(part, max_len))

    if path.is_absolute():
        safe = Path(cleaned_parts[0])
        for part in cleaned_parts[1:]:
            safe /= part
    else:
        safe = Path(cleaned_parts[0]) if cleaned_parts else Path()
        for part in cleaned_parts[1:]:
            safe /= part

    return str(safe.resolve())


def request_wants_file_output(query: str) -> bool:
    q = _normalize_query_for_paths(query).lower()
    has_save_intent = any(k in q for k in ["save", "write to", "store in", "output/", "launchpad/"])
    has_file_hint = any(ext in q for ext in [".md", ".txt", ".json", ".py", ".csv", ".yaml", ".yml"])
    return has_save_intent or has_file_hint


def choose_target_file_from_query(query: str) -> str:
    q = _normalize_query_for_paths(query)
    paths = re.findall(r'([A-Za-z0-9_\-./\\]+\.[A-Za-z0-9]+)', q)

    for candidate in paths:
        requested = normalize_path_text(candidate)
        files = parse_list_files()

        exact = [f for f in files if normalize_path_text(f).endswith(requested)]
        if exact:
            return exact[0]

        base = Path(requested).name
        basename_hits = [f for f in files if Path(normalize_path_text(f)).name == base]
        if basename_hits:
            return basename_hits[0]

    return ""


def _infer_default_extension(query: str) -> str:
    q = query.lower()

    if any(ext in q for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".sql"]):
        for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".sql"]:
            if ext in q:
                return ext

    if any(k in q for k in ["code", "script", "utility", "program", "function", "class", "cli"]):
        return ".py"

    if any(k in q for k in ["json", ".json"]):
        return ".json"

    if any(k in q for k in ["yaml", "yml", ".yaml", ".yml"]):
        return ".yaml"

    # Default all design/plan/report/doc tasks to markdown, not txt.
    if any(
        k in q
        for k in [
            "plan",
            "pipeline",
            "architecture",
            "design",
            "module",
            "report",
            "strategy",
            "roadmap",
            "documentation",
            "readme",
            "guide",
            "rag",
        ]
    ):
        return ".md"

    return ".md"


def choose_output_path_from_query(query: str) -> str:
    q = _normalize_query_for_paths(query)

    m = re.search(r'([A-Za-z0-9_\-./\\]+/)<file>(\.[A-Za-z0-9]+)', q, flags=re.IGNORECASE)
    if m:
        directory = m.group(1)
        extension = m.group(2)
        filename = _slugify(q, 48)
        return ensure_safe_output_path(str(Path(directory) / f"{filename}{extension}"))

    m = re.search(r'([A-Za-z0-9_\-./\\]+/)<([A-Za-z0-9_\-]+)>(\.[A-Za-z0-9]+)', q, flags=re.IGNORECASE)
    if m:
        directory = m.group(1)
        placeholder = m.group(2).lower()
        extension = m.group(3)
        if placeholder in {"file", "name_file", "name-file", "filename"}:
            filename = _slugify(q, 48)
        else:
            filename = _slugify(placeholder, 32)
        return ensure_safe_output_path(str(Path(directory) / f"{filename}{extension}"))

    m = re.search(r'([A-Za-z0-9_\-./\\]+/)<([A-Za-z0-9_\-]+)(\.[A-Za-z0-9]+)>', q, flags=re.IGNORECASE)
    if m:
        directory = m.group(1)
        placeholder = m.group(2).lower()
        extension = m.group(3)
        filename = _slugify(q if placeholder == "file" else placeholder, 48)
        return ensure_safe_output_path(str(Path(directory) / f"{filename}{extension}"))

    # Explicit path without extension: save in output/foo/bar
    m = re.search(r'\b(?:save|write|store).+?\b(?:in|to)\s+([A-Za-z0-9_\-./\\]+/[A-Za-z0-9_\-]+)\b', q, flags=re.IGNORECASE)
    if m:
        base_path = m.group(1).replace("\\", "/")
        ext = _infer_default_extension(q)
        return ensure_safe_output_path(base_path + ext)

    paths = re.findall(r'([A-Za-z0-9_\-./\\]+\.(?:md|txt|json|py|csv|yaml|yml))', q, flags=re.IGNORECASE)
    if paths:
        chosen = paths[-1].replace("\\", "/")
        return ensure_safe_output_path(chosen)

    if request_wants_file_output(q):
        folder_match = re.search(r'\b([A-Za-z0-9_\-]+)/<', q)
        folder = folder_match.group(1) if folder_match else "output"
        ext = _infer_default_extension(q)
        filename = _slugify(q, 48)
        return ensure_safe_output_path(str(Path(folder) / f"{filename}{ext}"))

    return ""


def detect_task_type(query: str) -> str:
    q = _normalize_query_for_paths(query).lower()

    if any(k in q for k in ["debug", "error", "traceback", "fix bug", "bug fix", "exception"]):
        return "debugging"
    if any(k in q for k in ["test", "pytest", "unit test", "integration test"]):
        return "testing"
    if ".csv" in q or ".sqlite" in q or ".db" in q or "analyze" in q or "analyse" in q:
        return "data"
    if any(k in q for k in ["write code", "generate code", "create code", "implement", ".py", "script", "utility"]):
        return "code"
    if any(k in q for k in ["readme", "documentation", "doc", "guide", "module"]):
        return "documentation"
    return "general"


def infer_deliverable_mode(task_type: str, query: str, output_path: str) -> str:
    suffix = Path(output_path).suffix.lower() if output_path else ""

    if suffix in {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".sql"}:
        return "code"
    if task_type in {"code", "debugging", "testing"}:
        return "code"
    if task_type == "data":
        return "data"
    return "document"


def infer_depth_threshold(task_type: str, query: str) -> int:
    q = query.lower()

    if any(k in q for k in ["in depth", "deep", "detailed", "comprehensive", "very detailed"]):
        return 1400
    if task_type in {"documentation", "general"}:
        return 900
    if task_type == "data":
        return 500
    return 300


def extract_count_requirements(query: str) -> dict[str, int]:
    q = query.lower()

    for word, value in _NUMBER_WORDS.items():
        q = re.sub(rf"\b{word}\b", str(value), q)

    matches = re.findall(r"\b(\d+)\s+(weeks?|days?|files?|steps?|sections?|modules?|agents?)\b", q)
    result: dict[str, int] = {}
    for number, unit in matches:
        result[unit.rstrip("s")] = int(number)
    return result


def extract_expected_sections_from_query(query: str) -> list[str]:
    q = query.lower()
    sections: list[str] = []

    if "will have" in q:
        tail = q.split("will have", 1)[1]
        tail = re.split(r"[.:\n]", tail)[0]
        parts = re.split(r",|\band\b", tail)
        for part in parts:
            part = re.sub(r"[^a-z0-9\s\-]", " ", part).strip()
            if 3 <= len(part) <= 40:
                sections.append(part)

    common_terms = [
        "learning objective",
        "concept",
        "topics",
        "exercise",
        "deliverables",
        "overview",
        "implementation",
        "deployment",
        "monitoring",
        "evaluation",
        "tradeoffs",
        "risks",
        "timeline",
        "milestones",
        "summary",
        "outputs",
        "ingestion",
        "chunking",
        "embedding",
        "indexing",
        "retrieval",
        "augmentation",
        "generation",
    ]
    for term in common_terms:
        if term in q and term not in sections:
            sections.append(term)

    cleaned: list[str] = []
    for item in sections:
        item = re.sub(r"\s+", " ", item).strip(" -_")
        if item and item not in cleaned:
            cleaned.append(item)
    return cleaned[:20]


def build_memory_context(query: str, session_memory: SessionMemory, vector_store: FaissVectorStore) -> str:
    fact_hits = session_memory.search_facts(query, limit=5)
    vector_hits = vector_store.search(query, k=3)
    return (
        "Recent session context:\n"
        f"{session_memory.format_recent_context()}\n\n"
        "Long-term facts:\n"
        f"{session_memory.format_fact_results(fact_hits)}\n\n"
        "Vector recall:\n"
        f"{vector_store.format_search_results(vector_hits)}"
    )


def strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    return text


def extract_code_block_or_raw(text: str) -> str:
    fenced = re.findall(r"```(?:python|py|bash|json|yaml|sql)?\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        longest = max(fenced, key=len)
        return longest.strip()
    return strip_markdown_fences(text)
```


===== FILE: nexus_ai/logger.py =====

```python
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
```


===== FILE: nexus_ai/main.py =====

```python
from __future__ import annotations

import asyncio
import logging

from autogen_core import AgentId, SingleThreadedAgentRuntime

from memory.session_memory import SessionMemory
from memory.vector_store import FaissVectorStore
from nexus_ai.agents.analyst import AnalystAgent
from nexus_ai.agents.coder import CoderAgent
from nexus_ai.agents.completion_checker import CompletionCheckerAgent
from nexus_ai.agents.critic import CriticAgent
from nexus_ai.agents.optimizer import OptimizerAgent
from nexus_ai.agents.orchestrator import OrchestratorAgent
from nexus_ai.agents.planner import PlannerAgent
from nexus_ai.agents.reporter import ReporterAgent
from nexus_ai.agents.researcher import ResearcherAgent
from nexus_ai.agents.toolsmith import ToolsmithAgent
from nexus_ai.agents.validator import ValidatorAgent
from nexus_ai.config import get_nexus_settings
from nexus_ai.logger import NexusLogger
from nexus_ai.models import NexusTask
from utils.llm_factory import build_text_model_client


async def main() -> None:
    settings = get_nexus_settings()

    if settings.debug_mode:
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("autogen_core").setLevel(logging.DEBUG)

    model_client = build_text_model_client(settings)
    nexus_logger = NexusLogger(settings.log_dir, debug_mode=settings.debug_mode)
    session_memory = SessionMemory(db_path=settings.session_db_path, max_turns=10)
    vector_store = FaissVectorStore(
        index_path=settings.vector_index_path,
        metadata_path=settings.vector_metadata_path,
        dim=1024,
    )

    runtime = SingleThreadedAgentRuntime()

    await PlannerAgent.register(runtime, "planner", lambda: PlannerAgent("planner", model_client, nexus_logger, settings.debug_mode))
    await ResearcherAgent.register(runtime, "researcher", lambda: ResearcherAgent("researcher", model_client, nexus_logger, settings.debug_mode))
    await CoderAgent.register(runtime, "coder", lambda: CoderAgent("coder", model_client, nexus_logger, settings.debug_mode))
    await AnalystAgent.register(runtime, "analyst", lambda: AnalystAgent("analyst", model_client, nexus_logger, settings.debug_mode))
    await CriticAgent.register(runtime, "critic", lambda: CriticAgent("critic", model_client, nexus_logger, settings.debug_mode))
    await OptimizerAgent.register(runtime, "optimizer", lambda: OptimizerAgent("optimizer", model_client, nexus_logger, settings.debug_mode))
    await CompletionCheckerAgent.register(
        runtime,
        "completion_checker",
        lambda: CompletionCheckerAgent("completion_checker", model_client, nexus_logger, settings.debug_mode),
    )
    await ToolsmithAgent.register(
        runtime,
        "toolsmith",
        lambda: ToolsmithAgent("toolsmith", model_client, nexus_logger, settings.debug_mode),
    )
    await ValidatorAgent.register(runtime, "validator", lambda: ValidatorAgent("validator", model_client, nexus_logger, settings.debug_mode))
    await ReporterAgent.register(runtime, "reporter", lambda: ReporterAgent("reporter", model_client, nexus_logger, settings.debug_mode))
    await OrchestratorAgent.register(
        runtime,
        "orchestrator",
        lambda: OrchestratorAgent(
            "orchestrator",
            model_client,
            nexus_logger,
            session_memory,
            vector_store,
            settings.debug_mode,
        ),
    )

    runtime.start()

    try:
        user_query = input("\nEnter your NEXUS AI task: ").strip()
        if not user_query:
            print("No task entered. Exiting.")
            return

        result = await runtime.send_message(
            NexusTask(query=user_query),
            AgentId("orchestrator", "default"),
        )

        print("\n" + "=" * 80)
        print("NEXUS AI FINAL ANSWER")
        print("=" * 80)
        print(result.final_answer)

        print("\n" + "=" * 80)
        print("EXECUTION TREE")
        print("=" * 80)
        print(result.execution_tree)

        print("\n" + "=" * 80)
        print("VALIDATION ISSUES")
        print("=" * 80)
        if result.validation_issues:
            for issue in result.validation_issues:
                print(f"- {issue}")
        else:
            print("No issues reported.")

        print("\n" + "=" * 80)
        print("LOG FILE")
        print("=" * 80)
        print(result.log_path)
    finally:
        await runtime.stop_when_idle()
        if hasattr(model_client, "close"):
            await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
```


===== FILE: nexus_ai/models.py =====

```python
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
```


===== FILE: tools/__init__.py =====

```python

```


===== FILE: tools/code_executor.py =====

```python
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
```


===== FILE: tools/db_agent.py =====

```python
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from autogen_core import MessageContext, RoutedAgent, message_handler

from models.day3_messages import DBInspection, FileInspection
from utils.day3_helpers import parse_json


DATA_DIR = Path("data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)


def preview_csv(csv_path: str, limit: int = 5) -> str:
    """Preview CSV rows."""
    file_path = Path(csv_path).resolve()
    if not file_path.exists():
        return json.dumps({"error": f"CSV not found: {file_path}"}, indent=2)

    try:
        rows = []
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if idx >= limit:
                    break
                rows.append(row)
        return json.dumps({"rows": rows, "preview_count": len(rows)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def csv_columns(csv_path: str) -> str:
    """Return CSV columns."""
    file_path = Path(csv_path).resolve()
    if not file_path.exists():
        return json.dumps({"error": f"CSV not found: {file_path}"}, indent=2)

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
        return json.dumps({"columns": headers}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def csv_schema(csv_path: str, sample_rows: int = 25) -> str:
    """Infer CSV schema."""
    file_path = Path(csv_path).resolve()
    if not file_path.exists():
        return json.dumps({"error": f"CSV not found: {file_path}"}, indent=2)

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = []
            for idx, row in enumerate(reader):
                if idx >= sample_rows:
                    break
                rows.append(row)

        schema = []
        for col in headers:
            values = [str(r.get(col, "")).strip() for r in rows]
            non_empty = [v for v in values if v != ""]
            numeric_count = 0
            for v in non_empty:
                try:
                    float(v.replace(",", ""))
                    numeric_count += 1
                except Exception:
                    pass

            if non_empty and numeric_count == len(non_empty):
                inferred = "numeric"
            elif non_empty:
                inferred = "text"
            else:
                inferred = "unknown"

            schema.append(
                {
                    "column": col,
                    "inferred_type": inferred,
                    "non_empty_sample_count": len(non_empty),
                }
            )

        return json.dumps({"schema": schema}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def import_csv_to_sqlite(
    csv_path: str,
    db_path: str = "data/day3_temp.sqlite",
    table_name: str = "data_table",
) -> str:
    """Import CSV into SQLite."""
    csv_file = Path(csv_path).resolve()
    db_file = Path(db_path).resolve()

    if not csv_file.exists():
        return json.dumps({"error": f"CSV not found: {csv_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        with open(csv_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)

            cols = ", ".join([f'"{h}" TEXT' for h in headers])
            cur.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            cur.execute(f'CREATE TABLE "{table_name}" ({cols})')

            placeholders = ", ".join(["?"] * len(headers))
            insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
            cur.executemany(insert_sql, reader)

        conn.commit()
        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        row_count = cur.fetchone()[0]
        conn.close()

        return json.dumps(
            {
                "status": "ok",
                "db_path": str(db_file),
                "table_name": table_name,
                "rows_imported": row_count,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def list_sqlite_tables(db_path: str) -> str:
    """List SQLite tables."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        rows = [row[0] for row in cur.fetchall()]
        conn.close()
        return json.dumps({"tables": rows}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def sqlite_table_schema(db_path: str, table_name: str) -> str:
    """Return SQLite table schema."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute(f'PRAGMA table_info("{table_name}")')
        rows = cur.fetchall()
        conn.close()

        columns = [
            {
                "cid": r[0],
                "name": r[1],
                "type": r[2],
                "notnull": r[3],
                "default_value": r[4],
                "pk": r[5],
            }
            for r in rows
        ]
        return json.dumps({"table_name": table_name, "columns": columns}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def sqlite_table_preview(db_path: str, table_name: str, limit: int = 5) -> str:
    """Preview SQLite rows."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM "{table_name}" LIMIT {int(limit)}')
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return json.dumps({"table_name": table_name, "rows": rows}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def query_sqlite(db_path: str, sql: str) -> str:
    """Run SQLite query."""
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        return json.dumps({"error": f"Database not found: {db_file}"}, indent=2)

    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return json.dumps({"rows": rows, "count": len(rows)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


class DBAgent(RoutedAgent):
    def __init__(self, name: str, debug_mode: bool = False) -> None:
        super().__init__(name)
        self._debug_mode = debug_mode

    def _debug(self, text: str) -> None:
        if self._debug_mode:
            print(text)

    @message_handler
    async def handle_file_inspection(self, message: FileInspection, ctx: MessageContext) -> DBInspection:
        self._debug("[db_agent] started")

        columns: list[str] = []
        preview_rows: list[dict[str, Any]] = []
        db_path = ""
        table_name = ""

        if message.intent == "code_generation":
            summary = "DB inspection not needed for code generation."
        elif not message.exists:
            summary = "No file available for DB/CSV inspection."
        elif message.file_type == "csv":
            columns_info = parse_json(csv_columns(message.file_path))
            schema_info = parse_json(csv_schema(message.file_path))
            preview_info = parse_json(preview_csv(message.file_path, limit=5))
            import_info = parse_json(import_csv_to_sqlite(message.file_path))

            columns = columns_info.get("columns", []) or []
            preview_rows = preview_info.get("rows", []) or []
            db_path = str(import_info.get("db_path", ""))
            table_name = str(import_info.get("table_name", ""))

            summary = (
                f"CSV columns: {columns}\n"
                f"Schema sample: {schema_info.get('schema', [])[:5]}\n"
                f"Preview rows count: {len(preview_rows)}\n"
                f"Imported DB path: {db_path}\n"
                f"Imported table: {table_name}"
            )

        elif message.file_type == "sqlite":
            tables_info = parse_json(list_sqlite_tables(message.file_path))
            tables = tables_info.get("tables", []) or []

            db_path = message.file_path
            table_name = str(tables[0]) if tables else ""

            schema_info = parse_json(sqlite_table_schema(db_path, table_name)) if table_name else {}
            preview_info = parse_json(sqlite_table_preview(db_path, table_name, limit=5)) if table_name else {}

            columns = [c["name"] for c in schema_info.get("columns", [])] if schema_info else []
            preview_rows = preview_info.get("rows", []) if preview_info else []

            summary = (
                f"SQLite tables: {tables}\n"
                f"Chosen table: {table_name}\n"
                f"Columns: {columns}\n"
                f"Preview rows count: {len(preview_rows)}"
            )
        else:
            summary = "Structured DB/CSV inspection not applicable to this file."

        self._debug("[db_agent] finished")

        return DBInspection(
            query=message.query,
            intent=message.intent,
            file_path=message.file_path,
            output_path=message.output_path,
            file_type=message.file_type,
            requested_items=message.requested_items,
            columns=columns,
            preview=preview_rows,
            db_path=db_path,
            table_name=table_name,
            summary=summary,
        )
```


===== FILE: tools/file_agent.py =====

```python
from __future__ import annotations

import json
import re
from pathlib import Path

from autogen_core import MessageContext, RoutedAgent, message_handler

from models.day3_messages import Day3Task, FileInspection
from utils.day3_helpers import infer_language_from_path, is_code_extension, parse_json


WORKSPACE_DIR = Path("data").resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def file_exists(file_path: str) -> str:
    """Check file existence."""
    path = Path(file_path).resolve()
    return json.dumps(
        {
            "path": str(path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "suffix": path.suffix.lower(),
        },
        indent=2,
    )


def detect_file_type(file_path: str) -> str:
    """Detect file type."""
    path = Path(file_path).resolve()
    suffix = path.suffix.lower()

    if suffix == ".csv":
        file_type = "csv"
    elif suffix in {".db", ".sqlite"}:
        file_type = "sqlite"
    elif suffix in {".txt", ".md", ".json", ".py", ".log", ".yaml", ".yml", ".xml", ".html", ".css", ".js", ".ts"}:
        file_type = "text"
    else:
        file_type = "unknown"

    return json.dumps({"path": str(path), "file_type": file_type}, indent=2)


def read_text_file(file_path: str) -> str:
    """Read a text file."""
    path = Path(file_path).resolve()
    if not path.exists():
        return json.dumps({"error": f"File not found: {path}"}, indent=2)

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return json.dumps({"path": str(path), "content": content}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def write_text_file(file_path: str, content: str) -> str:
    """Write a text file."""
    path = Path(file_path).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return json.dumps({"status": "ok", "path": str(path)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def list_files(directory: str = "data") -> str:
    """List files recursively."""
    base = Path(directory).resolve()
    if not base.exists():
        return json.dumps({"error": f"Directory not found: {base}"}, indent=2)

    files = [str(p) for p in base.rglob("*") if p.is_file()]
    return json.dumps({"files": files, "count": len(files)}, indent=2)


def local_search_files(directory: str, query: str) -> str:
    """Search text in files."""
    base = Path(directory).resolve()
    if not base.exists():
        return json.dumps({"error": f"Directory not found: {base}"}, indent=2)

    matches = []
    query_lower = query.lower()

    for path in base.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            if query_lower in line.lower():
                matches.append(
                    {
                        "file": str(path),
                        "line_no": line_no,
                        "line": line.strip(),
                    }
                )

    return json.dumps({"matches": matches, "count": len(matches)}, indent=2)


class FileAgent(RoutedAgent):
    def __init__(self, name: str, debug_mode: bool = False) -> None:
        super().__init__(name)
        self._debug_mode = debug_mode

    def _debug(self, text: str) -> None:
        if self._debug_mode:
            print(text)

    def _extract_all_paths(self, query: str) -> list[str]:
        return re.findall(r'([A-Za-z0-9_\-./\\]+?\.[A-Za-z0-9]+)', query)

    def _detect_intent(self, query: str, output_path: str = "") -> str:
        q = query.lower()

        code_patterns = [
            "generate code",
            "generate a code",
            "write code",
            "write a code",
            "create code",
            "create a code",
            "implement",
            "create script",
            "write script",
            "build function",
            "write function",
            "generate function",
            "save it in",
            "save it to",
            "save it at",
            "save to",
            "save at",
            "save in",
        ]
        if any(p in q for p in code_patterns):
            return "code_generation"

        if output_path and is_code_extension(output_path):
            code_hints = [
                "code",
                "script",
                "function",
                "class",
                "program",
                "algorithm",
                "binary search",
                "sort",
                "api",
                "backend",
            ]
            if any(h in q for h in code_hints):
                return "code_generation"

        analysis_patterns = [
            "analyze",
            "analyse",
            "insight",
            "insights",
            "summary",
            "statistics",
            "profile dataset",
            "inspect data",
            "find",
            "which",
            "highest",
            "lowest",
        ]
        if any(p in q for p in analysis_patterns):
            return "analysis"

        return "general"

    def _requested_items(self, query: str) -> int:
        match = re.search(r'(\d+)\s+(insight|insights|points|items)', query.lower())
        if match:
            return max(1, int(match.group(1)))
        return 5

    @message_handler
    async def handle_task(self, message: Day3Task, ctx: MessageContext) -> FileInspection:
        self._debug("[file_agent] started")

        paths = self._extract_all_paths(message.query)
        output_path = paths[-1] if paths else ""
        intent = self._detect_intent(message.query, output_path=output_path)
        requested_items = self._requested_items(message.query)

        file_path = ""

        if intent == "code_generation":
            file_type = infer_language_from_path(output_path) if output_path else "python"
            summary = (
                f"Intent: code_generation\n"
                f"Output path: {str(Path(output_path).resolve()) if output_path else 'not provided'}\n"
                f"Language: {file_type}"
            )
            self._debug("[file_agent] finished")
            return FileInspection(
                query=message.query,
                intent=intent,
                file_path="",
                output_path=output_path,
                exists=False,
                file_type=file_type,
                requested_items=requested_items,
                summary=summary,
            )

        if paths:
            file_path = paths[0]
        else:
            files_info = parse_json(list_files("data"))
            files = files_info.get("files", [])
            if files:
                file_path = str(files[0])

        exists_info = parse_json(file_exists(file_path)) if file_path else {"exists": False, "path": ""}
        type_info = parse_json(detect_file_type(file_path)) if file_path else {"file_type": "unknown"}

        exists = bool(exists_info.get("exists", False))
        file_path = str(exists_info.get("path", file_path))
        file_type = str(type_info.get("file_type", "unknown"))

        search_hits = []
        if exists and file_type == "text":
            keywords = message.query.split()[:2]
            if keywords:
                search_hits = parse_json(local_search_files("data", keywords[0])).get("matches", [])[:3]

        summary = (
            f"Intent: {intent}\n"
            f"File path: {file_path or 'not found'}\n"
            f"Exists: {exists}\n"
            f"File type: {file_type}\n"
            f"Requested items: {requested_items}\n"
            f"Local matches found: {len(search_hits)}"
        )

        self._debug("[file_agent] finished")

        return FileInspection(
            query=message.query,
            intent=intent,
            file_path=file_path,
            output_path="",
            exists=exists,
            file_type=file_type,
            requested_items=requested_items,
            summary=summary,
        )
```


===== FILE: utils/day3_helpers.py =====

```python
import json
from pathlib import Path


def parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def truncate_text(text: str, limit: int = 6000) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def infer_language_from_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
        ".cs": "csharp",
        ".sql": "sql",
        ".sh": "bash",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return mapping.get(suffix, "python")


def is_code_extension(path: str) -> bool:
    return Path(path).suffix.lower() in {
        ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs",
        ".php", ".rb", ".cs", ".sql", ".sh", ".html", ".css",
        ".json", ".xml", ".yaml", ".yml",
    }
```


===== FILE: utils/execution_tree.py =====

```python
class ExecutionTree:

    def __init__(self):

        self.tree = {
            "planner": None,
            "workers": [],
            "reflection": None,
            "validator": None
        }

    def add_plan(self, steps):
        self.tree["planner"] = steps

    def add_worker_result(self, step, result):
        self.tree["workers"].append({
            "step": step,
            "result": result
        })

    def add_reflection(self, reflection):
        self.tree["reflection"] = reflection

    def add_validation(self, validation):
        self.tree["validator"] = validation

    def display(self):

        print("\nEXECUTION TREE\n")

        print("PLANNER:")
        for step in self.tree["planner"]:
            print(f"  ├─ {step}")

        print("\nWORKERS:")

        for w in self.tree["workers"]:
            print(f"  ├─ STEP: {w['step']}")
            print(f"      RESULT: {w['result'][:120]}...\n")

        print("REFLECTION:")
        print(self.tree["reflection"][:200], "\n")

        print("VALIDATION:")
        print(self.tree["validator"][:200])

        print("\n")
```


===== FILE: utils/llm_factory.py =====

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient


def _model_info() -> dict:
    return {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "structured_output": False,
        "family": "unknown",
    }


def build_text_model_client(settings):
    model_provider = getattr(settings, "model_provider", "api")

    if model_provider == "local":
        from clients.local_hf_client import LocalHFChatClient
        return LocalHFChatClient(model_path=settings.local_model)

    api_provider = getattr(settings, "api_provider", "openrouter")

    if api_provider == "openrouter":
        api_key = getattr(settings, "openrouter_api_key", "") or getattr(settings, "api_key", "")
        base_url = getattr(settings, "openrouter_base_url", "") or getattr(settings, "base_url", "https://openrouter.ai/api/v1")
        model = getattr(settings, "openrouter_model", "") or getattr(settings, "api_model", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing.")
        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            include_name_in_message=False,
            model_info=_model_info(),
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-OpenRouter-Title": "week9-day5-nexus-ai",
            },
        )

    if api_provider == "groq":
        api_key = getattr(settings, "groq_api_key", "")
        base_url = getattr(settings, "groq_base_url", "https://api.groq.com/openai/v1")
        model = getattr(settings, "groq_model", "llama-3.3-70b-versatile")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing.")
        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            include_name_in_message=False,
            model_info=_model_info(),
        )

    raise ValueError(f"Unsupported API provider: {api_provider}")
```
