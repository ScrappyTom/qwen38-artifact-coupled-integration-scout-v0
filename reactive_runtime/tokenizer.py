from __future__ import annotations

import json
import urllib.request
from typing import Any


def render_qwen_messages(messages: list[dict[str, Any]]) -> str:
    """Exact non-thinking Qwen string-message rendering used by b10434."""
    rendered: list[str] = []
    for index, message in enumerate(messages):
        role = message.get("role")
        content = str(message.get("content") or "").strip()
        if role == "system" and index == 0:
            if content:
                rendered.append(f"<|im_start|>system\n{content}<|im_end|>\n")
        elif role in {"user", "assistant"}:
            rendered.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")
        else:
            raise ValueError(f"unsupported role at message {index}: {role!r}")
    rendered.append("<|im_start|>assistant\n<think>\n\n</think>\n\n")
    return "".join(rendered)


class HttpExactTokenizer:
    """Use the frozen llama.cpp endpoints for rendering and token counting."""

    def __init__(self, base_url: str, *, timeout_seconds: int = 180) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            value = json.loads(response.read())
        if not isinstance(value, dict):
            raise RuntimeError(f"non-object response from {path}")
        return value

    def count_text(self, text: str) -> int:
        value = self._post(
            "/tokenize",
            {"content": text, "add_special": False, "parse_special": True},
        )
        tokens = value.get("tokens")
        if not isinstance(tokens, list) or not all(isinstance(item, int) for item in tokens):
            raise RuntimeError("/tokenize response lacks an integer token list")
        return len(tokens)

    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        return self.count_text(render_qwen_messages(messages))

    def server_render(self, messages: list[dict[str, Any]]) -> str:
        value = self._post(
            "/apply-template",
            {
                "messages": messages,
                "add_generation_prompt": True,
                "chat_template_kwargs": {
                    "enable_thinking": False,
                    "preserve_thinking": False,
                },
            },
        )
        prompt = value.get("prompt")
        if not isinstance(prompt, str):
            raise RuntimeError("/apply-template response lacks prompt")
        return prompt

    def assert_template_parity(self, messages: list[dict[str, Any]]) -> str:
        manual = render_qwen_messages(messages)
        server = self.server_render(messages)
        if manual != server:
            raise RuntimeError("manual and server Qwen template rendering differ")
        return server
