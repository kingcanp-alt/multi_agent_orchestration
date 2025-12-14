"""
LLM config (gpt-4o-mini, gpt-4o....).
"""

from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_llm_instance: Optional[ChatOpenAI] = None


def _create_openai_llm(
    model_name: str,
    base_url: Optional[str],
    temperature: float,
    max_output_tokens: int,
    request_timeout_seconds: int,
    api_key: Optional[str] = None,
) -> ChatOpenAI:
    """Return ChatOpenAI instance."""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY must be set! "
            "Please add to .env file"
        )
    
    return ChatOpenAI(
        model=model_name,
        base_url=base_url or None,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_output_tokens,
        timeout=request_timeout_seconds,
    )


def configure(config: Optional[dict] = None) -> None:
    """Set ChatOpenAI instance."""
    global _llm_instance

    config_dict = config or {}

    model_name = config_dict.get("model") or os.getenv("OPENAI_MODEL", "gpt-4.1")
    base_url = config_dict.get("api_base") or os.getenv("OPENAI_BASE_URL", None)
    api_key = config_dict.get("api_key") or os.getenv("OPENAI_API_KEY")
    temperature = float(config_dict.get("temperature") or os.getenv("OPENAI_TEMPERATURE", "0.0"))
    max_output_tokens = int(config_dict.get("max_tokens") or os.getenv("OPENAI_MAX_TOKENS", "256"))
    request_timeout = int(config_dict.get("timeout") or os.getenv("OPENAI_TIMEOUT", "45"))

    _llm_instance = _create_openai_llm(
        model_name=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        request_timeout_seconds=request_timeout,
    )


llm: Optional[ChatOpenAI] = None

if _llm_instance is None:
    configure({})
    llm = _llm_instance
