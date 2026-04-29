"""Telegram Bot API tool for broadcasting deal digests.

Uses httpx (already available via ADK dependencies) to call the Telegram
Bot API.  Supports HTML formatting for clean mobile display.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"


async def send_telegram_message(message: str) -> dict:
    """Send a formatted message to the configured Telegram chat.

    The message should use Telegram's HTML formatting:
      <b>bold</b>, <i>italic</i>, <a href="...">link</a>, <code>code</code>

    The tool reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the
    environment (loaded via .env by config.py).

    Args:
        message: The HTML-formatted message text to send.

    Returns:
        A dict with ``success`` (bool) and either ``message_id`` or ``error``.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        return {
            "success": False,
            "error": (
                "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID. "
                "Please set them in your .env file."
            ),
        }

    # Telegram limits messages to 4096 characters.
    # If longer, split into chunks.
    chunks = _split_message(message, max_len=4096)
    sent_ids: list[int] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for chunk in chunks:
            url = f"{_TELEGRAM_API}/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            }
            try:
                resp = await client.post(url, json=payload)
                data = resp.json()
                if data.get("ok"):
                    sent_ids.append(data["result"]["message_id"])
                else:
                    logger.error("Telegram API error: %s", data)
                    return {
                        "success": False,
                        "error": data.get("description", "Unknown Telegram error"),
                    }
            except httpx.HTTPError as exc:
                logger.exception("HTTP error sending Telegram message")
                return {"success": False, "error": str(exc)}

    return {"success": True, "message_ids": sent_ids}


def _split_message(text: str, max_len: int = 4096) -> list[str]:
    """Split a long message into chunks that fit Telegram's limit."""
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at a newline near the limit
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks
