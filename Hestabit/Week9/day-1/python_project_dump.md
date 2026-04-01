p# Python Project Dump

## Folder Structure
```
.
├── AGENT-FUNDAMENTALS.MD
├── agents
│   ├── answer_agent.py
│   ├── __init__.py
│   ├── research_agent.py
│   └── summarizer_agent.py
├── .env
├── main.py
├── python_project_dump.md
└── requirements.txt

2 directories, 9 files
```

## FILE: ./agents/answer_agent.py

```py
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
```

## FILE: ./agents/__init__.py

```py
#packaging # tag::agents[]
#for everything
# end::agents[]

```

## FILE: ./agents/research_agent.py

```py
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
```

## FILE: ./agents/summarizer_agent.py

```py
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
```

## FILE: ./main.py

```py
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
```

## FILE: ./requirements.txt

```txt
autogen-agentchat
autogen-ext[openai]
openai
```

