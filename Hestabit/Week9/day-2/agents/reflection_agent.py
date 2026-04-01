from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext


def build_reflection_agent(model_client):
    return AssistantAgent(
        name="reflection_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=(
            "You are the Reflection Agent.\n"
            "Combine worker outputs into one improved draft.\n"
            "Return exactly this format:\n"
            "REFINED_DRAFT: <single paragraph>\n"
            "<END_REFLECTION>\n"
            "Rules:\n"
            "- Maximum 110 words\n"
            "- Single paragraph only\n"
            "- No bullets\n"
            "- No markdown\n"
            "- No intro\n"
            "- No conclusion\n"
            "- Stop after <END_REFLECTION>"
        ),
    )
