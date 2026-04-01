from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext


def build_research_agent(model_client):
    return AssistantAgent(
        name="research_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=(
            "You are the Research Agent.\n"
            "Your only job is to gather and organize useful factual information for the user's query.\n"
            "Do NOT summarize aggressively.\n"
            "Do NOT give the final answer to the user.\n"
            "Do NOT write in a polished end-user style.\n"
            "Output only research notes, key points, and relevant facts.\n"
            "Be structured and concise.\n"
            "Strict role boundary: research only."
        ),
    )