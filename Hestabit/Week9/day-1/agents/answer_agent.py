from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext


def build_answer_agent(model_client):
    return AssistantAgent(
        name="answer_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=(
            "You are the Answer Agent.\n"
            "Your only job is to create the final user-facing answer from the summary you receive.\n"
            "Do NOT behave like a researcher.\n"
            "Do NOT output raw notes.\n"
            "Do NOT mention internal agent workflow unless explicitly asked.\n"
            "Write a clear, accurate, polished final answer.\n"
            "Strict role boundary: final answer only."
        ),
    )