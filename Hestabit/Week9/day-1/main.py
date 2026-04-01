import asyncio
import os
from dotenv import load_dotenv

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.research_agent import build_research_agent
from agents.summarizer_agent import build_summarizer_agent
from agents.answer_agent import build_answer_agent

load_dotenv()

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def run_day1_flow(user_query: str) -> None:
    model_name = get_required_env("MODEL_NAME")
    base_url = get_required_env("BASE_URL")
    api_key = os.getenv("API_KEY", "lm-studio")
    temperature = float(os.getenv("TEMPERATURE", "0.2"))

    model_client = OpenAIChatCompletionClient(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        model_info=ModelInfo(
            vision=False,
            function_calling=False,
            json_output=False,
            family="unknown",
            structured_output=False,
        ),
    )

    research_agent = build_research_agent(model_client)
    summarizer_agent = build_summarizer_agent(model_client)
    answer_agent = build_answer_agent(model_client)

    cancellation_token = CancellationToken()

    research_response = await research_agent.on_messages(
        [TextMessage(content=user_query, source="user")],
        cancellation_token,
    )
    research_notes = research_response.chat_message.content

    summary_response = await summarizer_agent.on_messages(
        [
            TextMessage(
                content=(
                    "Summarize the following research notes into a compact, high-value summary.\n\n"
                    f"RESEARCH NOTES:\n{research_notes}"
                ),
                source="research_agent",
            )
        ],
        cancellation_token,
    )
    summary_text = summary_response.chat_message.content

    final_response = await answer_agent.on_messages(
        [
            TextMessage(
                content=(
                    "Create the final answer for the user using the summary below.\n\n"
                    f"SUMMARY:\n{summary_text}"
                ),
                source="summarizer_agent",
            )
        ],
        cancellation_token,
    )
    final_answer = final_response.chat_message.content

    print("\n" + "=" * 80)
    print("USER QUERY")
    print("=" * 80)
    print(user_query)

    print("\n" + "=" * 80)
    print("RESEARCH AGENT OUTPUT")
    print("=" * 80)
    print(research_notes)

    print("\n" + "=" * 80)
    print("SUMMARIZER AGENT OUTPUT")
    print("=" * 80)
    print(summary_text)

    print("\n" + "=" * 80)
    print("ANSWER AGENT OUTPUT")
    print("=" * 80)
    print(final_answer)

    await model_client.close()


if __name__ == "__main__":
    user_query = input("Enter your query: ").strip()
    asyncio.run(run_day1_flow(user_query))