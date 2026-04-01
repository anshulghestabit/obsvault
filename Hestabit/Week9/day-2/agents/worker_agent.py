from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext


WORKER_REGISTRY = {
    "research": (
        "You are a Research Worker.\n"
        "Your job is to gather relevant points, concepts, facts, examples, and structured notes.\n"
        "Do not produce the final polished answer.\n"
        "Be concise but useful.\n"
        "Strict role boundary: research only."
    ),
    "analysis": (
        "You are an Analysis Worker.\n"
        "Your job is to analyze the task deeply, identify relationships, tradeoffs, assumptions, risks, and logic.\n"
        "Do not produce the final polished answer.\n"
        "Strict role boundary: analysis only."
    ),
    "writer": (
        "You are a Writing Worker.\n"
        "Your job is to draft a clean, readable explanation from the assigned task only.\n"
        "Do not act as validator.\n"
        "Do not invent extra scope.\n"
        "Strict role boundary: writing only."
    ),
}


def build_worker_agent(model_client, role: str, worker_id: int):
    role = role.lower().strip()

    if role not in WORKER_REGISTRY:
        role = "analysis"

    return AssistantAgent(
        name=f"{role}_worker_{worker_id}",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=WORKER_REGISTRY[role],
    )
