from autogen_ext.models.openai import OpenAIChatCompletionClient


def _model_info() -> dict:
    return {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "structured_output": False,
        "family": "unknown",
    }


def build_text_model_client(settings):
    model_provider = getattr(settings, "model_provider", "lmstudio")

    if model_provider == "lmstudio":
        base_url = getattr(settings, "lmstudio_base_url", "http://127.0.0.1:1234/v1")
        api_key = getattr(settings, "lmstudio_api_key", "lm-studio")
        model = getattr(settings, "lmstudio_model", "")

        if not model:
            raise ValueError("LMSTUDIO_MODEL is missing.")

        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            include_name_in_message=False,
            model_info=_model_info(),
        )

    if model_provider == "openrouter":
        api_key = getattr(settings, "openrouter_api_key", "")
        base_url = getattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1")
        model = getattr(settings, "openrouter_model", "")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing.")
        if not model:
            raise ValueError("OPENROUTER_MODEL is missing.")

        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            include_name_in_message=False,
            model_info=_model_info(),
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-OpenRouter-Title": "week9-day5-nexus-ai",
            },
        )

    if model_provider == "groq":
        api_key = getattr(settings, "groq_api_key", "")
        base_url = getattr(settings, "groq_base_url", "https://api.groq.com/openai/v1")
        model = getattr(settings, "groq_model", "")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing.")
        if not model:
            raise ValueError("GROQ_MODEL is missing.")

        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            include_name_in_message=False,
            model_info=_model_info(),
        )

    raise ValueError(f"Unsupported MODEL_PROVIDER: {model_provider}")
