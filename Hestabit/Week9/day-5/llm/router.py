from config import MODEL_PROVIDER


def generate(system_prompt, user_prompt):

    if MODEL_PROVIDER == "local":
        from llm.local_llm import generate_local
        return generate_local(system_prompt, user_prompt)

    elif MODEL_PROVIDER == "api":
        from llm.api_llm import generate_api
        return generate_api(system_prompt, user_prompt)

    else:
        raise ValueError("Invalid model provider")