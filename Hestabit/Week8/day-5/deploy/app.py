import uuid
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from deploy.model_loader import get_model
from deploy.config import (
    SYSTEM_PROMPT,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    TOP_K
)
from deploy.logger import logger


# ======================
# FastAPI App
# ======================

app = FastAPI(
    title="Local Medical LLM API",
    version="1.0"
)

# ======================
# Request Schemas
# ======================

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = MAX_TOKENS
    temperature: Optional[float] = TEMPERATURE
    top_p: Optional[float] = TOP_P
    top_k: Optional[int] = TOP_K


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = MAX_TOKENS
    temperature: Optional[float] = TEMPERATURE
    top_p: Optional[float] = TOP_P
    top_k: Optional[int] = TOP_K

# ======================
# Prompt Builders
# ======================

def build_generate_prompt(user_prompt: str) -> str:
    """Build a single-turn generation prompt."""
    try:
        return (
            f"<|system|> {SYSTEM_PROMPT} </s>\n"
            f"<|user|> {user_prompt} </s>\n"
            f"<|assistant|>"
        )
    except Exception as exc:
        raise ValueError("failed to build generate prompt") from exc


def build_chat_prompt(messages: List[ChatMessage]) -> str:
    """Build a multi-turn chat prompt."""
    try:
        prompt = f"<|system|> {SYSTEM_PROMPT} </s>\n"
        for msg in messages:
            if msg.role == "user":
                prompt += f"<|user|> {msg.content} </s>\n"
            elif msg.role == "assistant":
                prompt += f"<|assistant|> {msg.content} </s>\n"
        prompt += "<|assistant|>"
        return prompt
    except Exception as exc:
        raise ValueError("failed to build chat prompt") from exc

# ======================
# STREAMING GENERATE
# ======================

@app.post("/generate")
def generate(request: GenerateRequest):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    endpoint = "/generate"

    logger.info(
        f"START | endpoint={endpoint} | request_id={request_id}"
    )

    try:
        model = get_model()
        prompt = build_generate_prompt(request.prompt)
    except Exception as exc:
        logger.exception(
            f"ERROR | endpoint={endpoint} | request_id={request_id} | detail={exc}"
        )
        raise HTTPException(status_code=500, detail="failed to initialize generation") from exc

    def stream_llm():
        try:
            for chunk in model(
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                stream=True
            ):
                try:
                    text = chunk["choices"][0]["text"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise ValueError("invalid streaming response chunk") from exc

                if text:
                    yield text

            latency = round(time.time() - start_time, 3)
            logger.info(
                f"END   | endpoint={endpoint} | request_id={request_id} | latency_sec={latency}"
            )
        except Exception as exc:
            logger.exception(
                f"ERROR | endpoint={endpoint} | request_id={request_id} | detail={exc}"
            )
            raise

    return StreamingResponse(
        stream_llm(),
        media_type="text/plain",
        headers={"X-Request-ID": request_id}
    )

# ======================
# STREAMING CHAT
# ======================

@app.post("/chat")
def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    endpoint = "/chat"

    logger.info(
        f"START | endpoint={endpoint} | request_id={request_id} | messages={len(request.messages)}"
    )

    try:
        model = get_model()
        prompt = build_chat_prompt(request.messages)
    except Exception as exc:
        logger.exception(
            f"ERROR | endpoint={endpoint} | request_id={request_id} | detail={exc}"
        )
        raise HTTPException(status_code=500, detail="failed to initialize chat") from exc

    def stream_llm():
        try:
            for chunk in model(
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                stream=True
            ):
                try:
                    text = chunk["choices"][0]["text"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise ValueError("invalid streaming response chunk") from exc

                if text:
                    yield text

            latency = round(time.time() - start_time, 3)
            logger.info(
                f"END   | endpoint={endpoint} | request_id={request_id} | latency_sec={latency}"
            )
        except Exception as exc:
            logger.exception(
                f"ERROR | endpoint={endpoint} | request_id={request_id} | detail={exc}"
            )
            raise

    return StreamingResponse(
        stream_llm(),
        media_type="text/plain",
        headers={"X-Request-ID": request_id}
    )
