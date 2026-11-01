"""Low-level HTTP client and streaming generators for local Ollama daemon."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Generator, List, Tuple

logger = logging.getLogger("ollama_client")


def is_ollama_online(api_base: str = "http://127.0.0.1:11434") -> bool:
    """Check if local Ollama daemon is responding.

    Tries 127.0.0.1 first to bypass Windows IPv6 resolution latency on localhost.
    """
    candidates = ["http://127.0.0.1:11434", api_base]
    seen: set = set()
    unique_candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for base in unique_candidates:
        try:
            url = f"{base.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with opener.open(req, timeout=0.4) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            continue
    return False


def call_ollama_chat_stream(
    user_prompt: str,
    api_base: str = "http://127.0.0.1:11434",
    model_name: str = "llama3:8b",
    system_prompt: str = "",
    history: List[dict] = None,
    temperature: float = 0.5,
) -> Generator[str, None, None]:
    """Call Ollama /api/chat with streaming enabled, yielding text pieces."""
    url = f"{api_base.rstrip('/')}/api/chat"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": 256,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    with opener.open(req, timeout=120) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            try:
                chunk = json.loads(line_str)
            except json.JSONDecodeError:
                continue
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                yield piece
            if chunk.get("done", False):
                break


def call_ollama_chat(
    user_prompt: str,
    api_base: str = "http://127.0.0.1:11434",
    model_name: str = "llama3:8b",
    system_prompt: str = "",
    history: List[dict] = None,
    temperature: float = 0.5,
    stream: bool = False,
    fallback_fn=None,
):
    """Call Ollama /api/chat synchronously or as stream."""
    if stream:
        return call_ollama_chat_stream(
            user_prompt=user_prompt,
            api_base=api_base,
            model_name=model_name,
            system_prompt=system_prompt,
            history=history,
            temperature=temperature,
        )
    try:
        chunks = call_ollama_chat_stream(
            user_prompt=user_prompt,
            api_base=api_base,
            model_name=model_name,
            system_prompt=system_prompt,
            history=history,
            temperature=temperature,
        )
        full = "".join(chunks).strip()
        return full or (fallback_fn() if fallback_fn else "")
    except Exception as err:
        logger.warning("Ollama call failed or timed out (%s). Using fallback template.", err)
        return fallback_fn() if fallback_fn else ""


def visible_only(chunks, sink: list) -> Generator[str, None, None]:
    """Yield visible text chunks while collecting the complete raw stream in sink.

    Stops yielding visible text as soon as control tags like QUICK_REPLIES,
    SLOT_UPDATE, or bracketed control syntax appear.
    """
    stopped = False
    buffer = ""
    control_pattern = re.compile(
        r"(\[?\s*(?:QUICK_REPLIES|SLOT_UPDATE)\b|\[\s*\"|\[\s*\{|```)",
        re.IGNORECASE,
    )

    for piece in chunks:
        sink.append(piece)
        if stopped:
            continue

        buffer += piece
        match = control_pattern.search(buffer)
        if match:
            stopped = True
            visible_text = buffer[: match.start()]
            if visible_text:
                yield visible_text
            buffer = ""
        else:
            partial_match = re.search(
                r"(\[|\[?\s*Q(?:U(?:I(?:C(?:K(?:_(?:R(?:E(?:P(?:L(?:I(?:E(?:S)?)?)?)?)?)?)?)?)?)?)?)?$|\[?\s*S(?:L(?:O(?:T(?:_(?:U(?:P(?:D(?:A(?:T(?:E)?)?)?)?)?)?)?)?)?)?$|`{1,3}$)",
                buffer,
                re.IGNORECASE,
            )
            if partial_match:
                safe_len = partial_match.start()
                safe_chunk = buffer[:safe_len]
                buffer = buffer[safe_len:]
                if safe_chunk:
                    yield safe_chunk
            else:
                yield buffer
                buffer = ""

    if not stopped and buffer:
        yield buffer
