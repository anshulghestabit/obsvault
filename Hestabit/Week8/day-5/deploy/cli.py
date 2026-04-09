import requests
import sys

API_URL_CHAT = "http://localhost:8000/chat"

SYSTEM_PROMPT = (
    "You are a helpful medical assistant. "
    "Answer medical questions accurately and safely. "
    "Answer using clear bullet points."
)


def single_prompt_mode(prompt: str):
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 40
    }

    response = requests.post(API_URL_CHAT, json=payload, stream=True)

    if response.status_code != 200:
        print("Error communicating with backend")
        return

    for chunk in response.iter_content(chunk_size=None):
        if chunk:
            print(chunk.decode("utf-8"), end="", flush=True)

    print()


def interactive_chat_mode():
    print("\n🩺 Medical LLM CLI")
    print("Type 'exit' to quit.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("> ")

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        payload = {
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 40
        }

        response = requests.post(API_URL_CHAT, json=payload, stream=True)

        if response.status_code != 200:
            print("Error communicating with backend")
            continue

        print("\n--- Assistant ---")

        reply = ""
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                text = chunk.decode("utf-8")
                reply += text
                print(text, end="", flush=True)

        print()
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    if len(sys.argv) > 1: ## sys.argv is a list of CLI arguments .. 
        single_prompt_mode(" ".join(sys.argv[1:]))
    else:
        interactive_chat_mode()