#!/usr/bin/env python3
"""Explicit production smoke test for the configured OpenRouter model."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://openrouter.ai/api/v1"


class SmokeError(RuntimeError):
    pass


def request_json(
    url: str,
    api_key: str,
    payload: dict | None = None,
    timeout: float = 20,
) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        raise SmokeError(f"OpenRouter returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise SmokeError("OpenRouter request failed or timed out") from exc
    try:
        decoded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmokeError("OpenRouter returned invalid JSON") from exc
    if not isinstance(decoded, dict):
        raise SmokeError("OpenRouter returned an unexpected JSON value")
    return decoded


def model_is_available(payload: dict, model: str) -> bool:
    data = payload.get("data")
    if not isinstance(data, list):
        return False
    return any(isinstance(item, dict) and item.get("id") == model for item in data)


def completion_summary(payload: dict) -> dict:
    choices = payload.get("choices")
    usage = payload.get("usage")
    if not isinstance(choices, list) or not choices or not isinstance(usage, dict):
        raise SmokeError("Completion response is missing choices or usage")
    return {
        "model": payload.get("model"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cost": usage.get("cost"),
    }


def run_smoke(api_key: str, model: str) -> dict:
    if not api_key:
        raise SmokeError("OPENROUTER_API_KEY is empty")
    if not model:
        raise SmokeError("OPENROUTER_MODEL is empty")
    catalog = request_json(f"{BASE_URL}/models", api_key)
    if not model_is_available(catalog, model):
        raise SmokeError(f"Configured model is unavailable: {model}")
    completion = request_json(
        f"{BASE_URL}/chat/completions",
        api_key,
        {
            "model": model,
            "messages": [{"role": "user", "content": "Reply only OK"}],
            "max_tokens": 2,
        },
    )
    return completion_summary(completion)


def main() -> int:
    try:
        summary = run_smoke(
            os.getenv("OPENROUTER_API_KEY", ""),
            os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4-5").strip(),
        )
    except SmokeError as exc:
        print(f"OpenRouter smoke failed: {exc}")
        return 1
    print("OpenRouter smoke passed")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if summary["cost"] is None:
        print("Cost was not returned; no price was calculated from token counts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
