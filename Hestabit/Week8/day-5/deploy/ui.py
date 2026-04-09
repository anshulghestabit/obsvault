import streamlit as st
import requests
import uuid

API_BASE_URL = "http://backend:8000"
REQUEST_TIMEOUT = 120

st.set_page_config(
    page_title="Medical LLM Assistant",
    layout="wide"
)

def init_session_state() -> None:
    """Initialize stable session state values."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []


def apply_theme(theme_mode: str) -> None:
    """Apply a lightweight custom light/dark theme."""
    themes = {
        "Light": {
            "bg": "#f6f8fb",
            "panel": "#ffffff",
            "text": "#132238",
            "muted": "#566579",
            "border": "#dce5ef"
        },
        "Dark": {
            "bg": "#0f1724",
            "panel": "#162130",
            "text": "#e7eef7",
            "muted": "#9fb0c4",
            "border": "#2c3f55"
        }
    }
    selected = themes.get(theme_mode, themes["Light"])
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {selected['bg']};
                color: {selected['text']};
            }}
            [data-testid="stSidebar"] {{
                background: {selected['panel']};
                border-right: 1px solid {selected['border']};
            }}
            h1, h2, h3, p, label, div, span {{
                color: {selected['text']};
            }}
            .stChatMessage {{
                background: {selected['panel']};
                border: 1px solid {selected['border']};
                border-radius: 12px;
                padding: 0.4rem;
            }}
            .stCaption {{
                color: {selected['muted']};
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


def format_as_bullets(text: str) -> str:
    """Normalize multiline text into markdown bullet points."""
    lines = text.strip().split("\n")
    bullet_lines = []
    for line in lines:
        clean = line.strip()
        if clean:
            bullet_lines.append("- " + clean.lstrip("-*• ").strip())
    return "\n".join(bullet_lines)


def stream_response(response: requests.Response) -> str:
    """Stream bytes to UI and return accumulated text."""
    return st.write_stream(
        line.decode("utf-8")
        for line in response.iter_lines()
        if line
    )


def post_stream(endpoint: str, payload: dict) -> requests.Response:
    """Send a streaming request and validate HTTP response."""
    response = requests.post(
        f"{API_BASE_URL}{endpoint}",
        json=payload,
        stream=True,
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response


def render_sidebar() -> dict:
    """Render sidebar settings and return selected values."""
    st.sidebar.title("Settings")

    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []

    mode = st.sidebar.radio("Mode", ["Chat", "Single Prompt"])
    theme_mode = st.sidebar.radio("Theme", ["Light", "Dark"], index=0)
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    top_p = st.sidebar.slider("Top-P", 0.1, 1.0, 0.9, 0.05)
    top_k = st.sidebar.slider("Top-K", 1, 100, 40, 1)
    system_prompt = st.sidebar.text_area(
        "System Prompt",
        value="You are a helpful medical assistant. Answer clearly and accurately.",
        height=120
    )
    return {
        "mode": mode,
        "theme_mode": theme_mode,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "system_prompt": system_prompt
    }


def render_chat_mode(config: dict) -> None:
    """Render streaming chat mode."""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask something...")
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    payload = {
        "messages": [{"role": "system", "content": config["system_prompt"]}] + st.session_state.messages,
        "temperature": config["temperature"],
        "top_p": config["top_p"],
        "top_k": config["top_k"]
    }

    with st.chat_message("assistant"):
        try:
            response = post_stream("/chat", payload)
            full_response = stream_response(response)
            formatted = format_as_bullets(full_response)
        except requests.RequestException as exc:
            formatted = f"Unable to reach backend service: {exc}"
            st.error(formatted)

    st.session_state.messages.append({"role": "assistant", "content": formatted})


def render_single_prompt_mode(config: dict) -> None:
    """Render single-prompt streaming mode."""
    user_input = st.chat_input("Ask a medical question...")
    if not user_input:
        return

    with st.chat_message("user"):
        st.markdown(user_input)

    payload = {
        "prompt": user_input,
        "temperature": config["temperature"],
        "top_p": config["top_p"],
        "top_k": config["top_k"]
    }

    with st.chat_message("assistant"):
        try:
            response = post_stream("/generate", payload)
            full_response = stream_response(response)
            st.markdown(format_as_bullets(full_response))
        except requests.RequestException as exc:
            st.error(f"Unable to reach backend service: {exc}")


def main() -> None:
    """Run the Streamlit UI."""
    init_session_state()
    config = render_sidebar()
    apply_theme(config["theme_mode"])

    st.title("Medical Assistant")
    st.caption(f"Session: {st.session_state.session_id}")

    if config["mode"] == "Chat":
        render_chat_mode(config)
    else:
        render_single_prompt_mode(config)


if __name__ == "__main__":
    main()
