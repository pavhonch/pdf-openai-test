from collections.abc import Sequence

import httpx
from openai import APIError, APIStatusError, OpenAI

from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_BASE_URL,
    OPENROUTER_KEY_MISSING_MESSAGE,
    OPENROUTER_MODEL,
    OPENROUTER_SITE_URL,
)

_LLM_TIMEOUT = httpx.Timeout(15.0, read=180.0, write=60.0, pool=15.0)


class LLMError(Exception):
    pass


def _client() -> OpenAI:
    if not OPENROUTER_API_KEY:
        raise LLMError(OPENROUTER_KEY_MISSING_MESSAGE)
    headers: dict[str, str] = {}
    if OPENROUTER_SITE_URL:
        headers["HTTP-Referer"] = OPENROUTER_SITE_URL
    if OPENROUTER_APP_NAME:
        headers["X-Title"] = OPENROUTER_APP_NAME
    kwargs: dict = {
        "base_url": OPENROUTER_BASE_URL,
        "api_key": OPENROUTER_API_KEY,
        "timeout": _LLM_TIMEOUT,
    }
    if headers:
        kwargs["default_headers"] = headers
    return OpenAI(**kwargs)


def chat_completion(
    messages: Sequence[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    use_model = model or OPENROUTER_MODEL
    if not use_model:
        raise LLMError("OPENROUTER_MODEL is not set.")

    client = _client()
    try:
        response = client.chat.completions.create(
            model=use_model,
            messages=list(messages),
            temperature=temperature,
        )
    except httpx.TimeoutException:
        raise LLMError(
            "OpenRouter request timed out. Try again, or use a shorter document."
        ) from None
    except httpx.RequestError:
        raise LLMError(
            "Could not reach OpenRouter. Check your network and try again."
        ) from None
    except APIStatusError as e:
        msg = (e.message or "").strip()
        if len(msg) > 400:
            msg = msg[:397] + "..."
        raise LLMError(f"{msg} (OpenRouter HTTP error)") from e
    except APIError as e:
        msg = (e.message or "").strip()
        if len(msg) > 400:
            msg = msg[:397] + "..."
        raise LLMError(f"{msg} (OpenRouter API error)") from e
    except Exception as e:  # noqa: BLE001
        msg = str(e).strip().replace("\n", " ")
        if len(msg) > 400:
            msg = msg[:397] + "..."
        raise LLMError(
            f"{msg or 'Request failed'} (OpenRouter request failed)"
        ) from e

    choice = response.choices[0] if response.choices else None
    content = (choice.message.content if choice and choice.message else "") or ""
    content = content.strip()
    if not content:
        raise LLMError("The model returned an empty reply. Try again or pick another model.")
    return content
