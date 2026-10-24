"""Groq client wrapper using official groq SDK and python-dotenv."""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env
load_dotenv()


def get_groq_api_key() -> str:
    """Retrieve GROQ_API_KEY from environment."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise ValueError("GROQ_API_KEY is not set. Please define GROQ_API_KEY in your .env file or environment.")
    return key


def get_groq_model() -> str:
    """Retrieve GROQ_MODEL from environment, with sensible default."""
    return os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()


def get_groq_client(api_key: Optional[str] = None) -> Groq:
    """Create official Groq client with configured timeout."""
    key = api_key if api_key is not None else get_groq_api_key()
    return Groq(api_key=key, timeout=30.0)


def call_groq(
    messages: List[Dict[str, str]],
    client: Optional[Groq] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    timeout: float = 30.0,
    max_retries: int = 1,
) -> str:
    """
    Call Groq API with temperature 0.2, timeout 30s, json_object response format, and 1 retry.
    Returns JSON response string.
    """
    if client is None:
        client = get_groq_client()

    selected_model = model if model else get_groq_model()
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=selected_model,
                temperature=temperature,
                response_format={"type": "json_object"},
                timeout=timeout,
            )
            content = chat_completion.choices[0].message.content
            if content is None:
                raise ValueError("Groq returned an empty response.")
            return content
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue
            raise last_error
