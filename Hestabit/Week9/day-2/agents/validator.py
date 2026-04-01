from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext


def build_validator_agent(model_client):
    return AssistantAgent(
        name="validator_agent",
        model_client=model_client,
        model_context=BufferedChatCompletionContext(buffer_size=10),
        system_message=(
            "You are the Validator Agent.\n"
            "Your job is to review the reflected draft for errors, contradictions, missing pieces, and weak logic.\n"
            "If the draft is acceptable, return:\n"
            "STATUS: PASS\n"
            "FINAL_ANSWER:\n"
            "<final answer>\n\n"
            "If the draft needs work, return:\n"
            "STATUS: NEEDS_REVISION\n"
            "ISSUES:\n"
            "- issue 1\n"
            "- issue 2\n"
            "FINAL_ANSWER:\n"
            "<best corrected answer you can provide>\n"
            "Always include FINAL_ANSWER."
        ),
    )
