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
    model_provider = getattr(settings, "model_provider", "api")

    if model_provider == "local":
        from clients.local_hf_client import LocalHFChatClient
        return LocalHFChatClient(model_path=settings.local_model)

    api_provider = getattr(settings, "api_provider", "openrouter")

    if api_provider == "openrouter":
        api_key = getattr(settings, "openrouter_api_key", "") or getattr(settings, "api_key", "")
        base_url = getattr(settings, "openrouter_base_url", "") or getattr(settings, "base_url", "https://openrouter.ai/api/v1")
        model = getattr(settings, "openrouter_model", "") or getattr(settings, "api_model", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing.")
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

    if api_provider == "groq":
        api_key = getattr(settings, "groq_api_key", "")
        base_url = getattr(settings, "groq_base_url", "https://api.groq.com/openai/v1")
        model = getattr(settings, "groq_model", "llama-3.3-70b-versatile")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing.")
        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            include_name_in_message=False,
            model_info=_model_info(),
        )

    raise ValueError(f"Unsupported API provider: {api_provider}")