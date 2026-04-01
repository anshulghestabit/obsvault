import re

from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext


def build_planner_agent(model_client):
    return AssistantAgent(
        name="planner_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=(
            "You are the Planner Agent.\n"
            "Your only job is to split the user's query into exactly 3 worker tasks.\n"
            "Use only these roles: research, analysis, writer.\n"
            "Output exactly 4 lines and nothing else.\n"
            "Line 1 format: STEP 1 | role=research | goal=<short task>\n"
            "Line 2 format: STEP 2 | role=analysis | goal=<short task>\n"
            "Line 3 format: STEP 3 | role=writer | goal=<short task>\n"
            "Line 4 must be exactly: <END_PLAN>\n"
            "Rules:\n"
            "- No introduction\n"
            "- No explanation\n"
            "- No markdown\n"
            "- Each goal must be under 18 words\n"
            "- Stop immediately after <END_PLAN>"
        ),
    )


def parse_plan(plan_text: str):
    steps = []
    pattern = re.compile(
        r"STEP\s*(\d+)\s*\|\s*role\s*=\s*([a-zA-Z_]+)\s*\|\s*goal\s*=\s*(.+)",
        re.IGNORECASE,
    )

    for line in plan_text.splitlines():
        line = line.strip()
        match = pattern.match(line)
        if match:
            steps.append(
                {
                    "step": int(match.group(1)),
                    "role": match.group(2).strip().lower(),
                    "goal": match.group(3).strip(),
                }
            )

    return steps
