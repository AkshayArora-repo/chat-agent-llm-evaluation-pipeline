from __future__ import annotations

"""Utility helpers for the recipe chatbot backend.

This module centralises the system prompt, environment loading, and the
model invocation logic (either via litellm or Intuit's llm-execution-svc).
"""

import os
from pathlib import Path
from typing import Final, List, Dict

import litellm  # type: ignore
import httpx
from dotenv import load_dotenv

# Ensure the .env file is loaded as early as possible. Prefer values from .env.
load_dotenv(override=True)

# --- Constants -------------------------------------------------------------------

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "recipe_system_prompt.md"
SYSTEM_PROMPT: Final[str] = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()

# Fetch configuration *after* we loaded the .env file.
MODEL_NAME: Final[str] = os.environ.get("MODEL_NAME", "gpt-4o-mini")

# llm-exec config (reintroduced). Two ways to supply auth:
# 1) Single-paste header via INTUIT_PRIVATEAUTH_HEADER
# 2) Individual fields (fallback) like INTUIT_APP_ID, INTUIT_APP_SECRET, etc.
LLM_EXEC_ENABLED: Final[bool] = os.environ.get("LLM_EXEC_ENABLED", "false").lower() == "true"
LLM_EXEC_BASE_URL: Final[str] = os.environ.get("LLM_EXEC_BASE_URL", "")
LLM_EXEC_MODEL_PATH: Final[str] = os.environ.get("LLM_EXEC_MODEL_PATH", "")

INTUIT_PRIVATEAUTH_HEADER: Final[str] = os.environ.get("INTUIT_PRIVATEAUTH_HEADER", "").strip()

INTUIT_EXPERIENCE_ID: Final[str] = os.environ.get("INTUIT_EXPERIENCE_ID", "").strip()
INTUIT_ORIGINATING_ASSETALIAS: Final[str] = os.environ.get("INTUIT_ORIGINATING_ASSETALIAS", "").strip()
INTUIT_TEST_HEADER: Final[str] = os.environ.get("INTUIT_TEST_HEADER", "").strip()


def _build_privateauth_header() -> str:
    """Return the single-paste PrivateAuth+ header.

    Raises a clear error if empty to keep behavior explicit and simple.
    """
    if not INTUIT_PRIVATEAUTH_HEADER:
        raise RuntimeError(
            "INTUIT_PRIVATEAUTH_HEADER is empty. Paste the full PrivateAuth+ header string in .env"
        )
    return INTUIT_PRIVATEAUTH_HEADER


def _call_llm_exec(current_messages: List[Dict[str, str]]) -> str:
    if not (LLM_EXEC_BASE_URL and LLM_EXEC_MODEL_PATH):
        raise RuntimeError("LLM exec enabled but base URL or model path missing")

    url = f"{LLM_EXEC_BASE_URL.rstrip('/')}/v3/{LLM_EXEC_MODEL_PATH}/chat/completions"
    headers = {
        "Authorization": _build_privateauth_header(),
        "Content-Type": "application/json",
        "intuit_experience_id": INTUIT_EXPERIENCE_ID,
        "intuit_originating_assetalias": INTUIT_ORIGINATING_ASSETALIAS,
    }
    if INTUIT_TEST_HEADER:
        headers["TEST"] = INTUIT_TEST_HEADER

    payload = {"messages": current_messages}
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"llm-exec error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


# --- Agent wrapper ---------------------------------------------------------------

def get_agent_response(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:  # noqa: WPS231
    """Call the underlying LLM either via *litellm* or llm-exec directly.

    Parameters
    ----------
    messages:
        The full conversation history. Each item is a dict with "role" and "content".

    Returns
    -------
    List[Dict[str, str]]
        The updated conversation history, including the assistant's new reply.
    """

    # Ensure the system prompt is always first.
    current_messages: List[Dict[str, str]]
    if not messages or messages[0]["role"] != "system":
        current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    else:
        current_messages = messages

    if LLM_EXEC_ENABLED:
        assistant_reply_content = _call_llm_exec(current_messages)
    else:
        completion = litellm.completion(
            model=MODEL_NAME,
            messages=current_messages,
        )
        assistant_reply_content = (
            completion["choices"][0]["message"]["content"]  # type: ignore[index]
            .strip()
        )

    updated_messages = current_messages + [{"role": "assistant", "content": assistant_reply_content}]
    return updated_messages