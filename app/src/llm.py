"""OpenAI client helpers."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src import config


def client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to app/.env")
    return OpenAI(api_key=api_key)


@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(3))
def chat_json(prompt: str) -> dict[str, Any]:
    response = client().chat.completions.create(
        model=config.openai_model(),
        messages=[
            {
                "role": "system",
                "content": "You return only valid JSON. No markdown fences.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
