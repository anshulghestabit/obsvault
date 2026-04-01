import asyncio
import os

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

from orchestrator.planner import build_planner_agent, parse_plan
from agents.worker_agent import build_worker_agent
from agents.reflection_agent import build_reflection_agent
from agents.validator import build_validator_agent


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_agent_status(agent_name: str, status: str):
    print(f"[{status}] {agent_name}")


def trim_to_marker(text: str, marker: str) -> str:
    if marker in text:
        return text.split(marker)[0].strip()
    return text.strip()


def trim_lines(text: str, max_lines: int) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:max_lines]).strip()


def trim_chars(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


def sanitize_output(text: str, marker: str, max_lines: int, max_chars: int) -> str:
    text = trim_to_marker(text, marker)
    text = trim_lines(text, max_lines)
    text = trim_chars(text, max_chars)
    return text


async def call_agent(agent, agent_name: str, source: str, prompt: str, marker: str, max_lines: int, max_chars: int, timeout_seconds: int):
    print_agent_status(agent_name, "STARTED")
    try:
        response = await asyncio.wait_for(
            agent.on_messages(
                [TextMessage(content=prompt, source=source)],
                CancellationToken(),
            ),
            timeout=timeout_seconds,
        )
        content = response.chat_message.content
        clean = sanitize_output(content, marker=marker, max_lines=max_lines, max_chars=max_chars)
        print_agent_status(agent_name, "FINISHED")
        return clean
    except asyncio.TimeoutError:
        print_agent_status(agent_name, "TIMEOUT")
        return f"TIMEOUT from {agent_name}"


def build_model_client():
    model_name = get_required_env("MODEL_NAME")
    base_url = get_required_env("BASE_URL")
    api_key = os.getenv("API_KEY", "lm-studio")
    temperature = float(os.getenv("TEMPERATURE", "0.05"))
    max_tokens = int(os.getenv("MAX_TOKENS", "220"))

    return OpenAIChatCompletionClient(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        model_info=ModelInfo(
            vision=False,
            function_calling=False,
            json_output=False,
            family="unknown",
            structured_output=False,
        ),
    )


def print_execution_tree(steps):
    print_banner("EXECUTION TREE")
    print("USER")
    print("└── PLANNER")
    for index, step in enumerate(steps, start=1):
        branch = "├──" if index < len(steps) else "└──"
        print(f"    {branch} WORKER_{step['step']} [{step['role']}]")
    print("        ↓")
    print("    REFLECTION")
    print("        ↓")
    print("    VALIDATOR")
    print("        ↓")
    print("    FINAL ANSWER")


async def run_worker(model_client, step, user_query: str, timeout_seconds: int):
    worker = build_worker_agent(
        model_client=model_client,
        role=step["role"],
        worker_id=step["step"],
    )

    prompt = (
        f"USER_QUERY: {user_query}\n"
        f"STEP: {step['step']}\n"
        f"ROLE: {step['role']}\n"
        f"GOAL: {step['goal']}\n"
    )

    output = await call_agent(
        agent=worker,
        agent_name=worker.name,
        source="planner_agent",
        prompt=prompt,
        marker="<END_WORK>",
        max_lines=80,
        max_chars=580,
        timeout_seconds=timeout_seconds,
    )

    return {
        "step": step["step"],
        "role": step["role"],
        "goal": step["goal"],
        "output": output,
    }


async def run_day2_flow(user_query: str):
    timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "90"))
    model_client = build_model_client()

    planner_agent = build_planner_agent(model_client)
    reflection_agent = build_reflection_agent(model_client)
    validator_agent = build_validator_agent(model_client)

    planner_prompt = (
        f"USER_QUERY: {user_query}\n"
        "Create the 3-step plan now."
    )

    raw_plan = await call_agent(
        agent=planner_agent,
        agent_name="planner_agent",
        source="user",
        prompt=planner_prompt,
        marker="<END_PLAN>",
        max_lines=3,
        max_chars=260,
        timeout_seconds=timeout_seconds,
    )

    steps = parse_plan(raw_plan)

    if len(steps) != 3:
        steps = [
            {"step": 1, "role": "research", "goal": "Find the main functions and features."},
            {"step": 2, "role": "analysis", "goal": "Explain components, data flow, and tradeoffs."},
            {"step": 3, "role": "writer", "goal": "Draft a short user-friendly architecture answer."},
        ]

    steps = sorted(steps, key=lambda x: x["step"])
    print_execution_tree(steps)

    worker_results = await asyncio.gather(
        *(run_worker(model_client, step, user_query, timeout_seconds) for step in steps)
    )

    combined_worker_text = "\n\n".join(
        [
            f"STEP {item['step']} | ROLE={item['role']} | GOAL={item['goal']}\n{item['output']}"
            for item in worker_results
        ]
    )

    reflection_prompt = (
        f"USER_QUERY: {user_query}\n\n"
        f"WORKER_OUTPUTS:\n{combined_worker_text}\n"
    )

    reflected_draft = await call_agent(
        agent=reflection_agent,
        agent_name="reflection_agent",
        source="workers",
        prompt=reflection_prompt,
        marker="<END_REFLECTION>",
        max_lines=2,
        max_chars=500,
        timeout_seconds=timeout_seconds,
    )

    validator_prompt = (
        f"USER_QUERY: {user_query}\n\n"
        f"DRAFT:\n{reflected_draft}\n"
    )

    validated_output = await call_agent(
        agent=validator_agent,
        agent_name="validator_agent",
        source="reflection_agent",
        prompt=validator_prompt,
        marker="TERMINATE",
        max_lines=3,
        max_chars=700,
        timeout_seconds=timeout_seconds,
    )

    print_banner("PLANNER OUTPUT")
    print(raw_plan)

    print_banner("PARALLEL WORKER OUTPUTS")
    for result in worker_results:
        print(f"\n--- STEP {result['step']} | {result['role'].upper()} ---")
        print(result["output"])

    print_banner("REFLECTION OUTPUT")
    print(reflected_draft)

    print_banner("VALIDATOR OUTPUT")
    print(validated_output)

    await model_client.close()


if __name__ == "__main__":
    query = input("Enter your query: ").strip()
    asyncio.run(run_day2_flow(query))
