from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext


def build_summarizer_agent(model_client):
    return AssistantAgent(
        name="summarizer_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=(
            "You are the Summarizer Agent.\n"
            "Your only job is to compress and organize the research notes provided to you.\n"
            "Do NOT introduce major new facts.\n"
            "Do NOT answer the user directly.\n"
            "Do NOT act like the research agent.\n"
            "Transform the input into a clean, compact, high-signal summary.\n"
            "Strict role boundary: summarization only."
        ),
    )