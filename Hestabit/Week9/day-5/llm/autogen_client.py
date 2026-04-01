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
