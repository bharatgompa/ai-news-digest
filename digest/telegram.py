"""Send the digest to a Telegram chat."""

import html
import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)

MAX_LEN = 4000  # Telegram limit is 4096 chars per message
STARS = {5: "🔥", 4: "⭐", 3: "•", 2: "·", 1: "·"}


def render(digest: dict, dashboard_url: str | None) -> list[str]:
    e = html.escape
    blocks = [f"<b>🗞 Daily Digest — {e(digest['date'])}</b>\n<i>{e(digest['headline'])}</i>"]
    for section in digest["sections"]:
        lines = [f"\n<b>{e(section['title'])}</b>"]
        for s in section["stories"]:
            lines.append(
                f"{STARS.get(s['importance'], '•')} <a href=\"{e(s['url'], quote=True)}\">{e(s['title'])}</a>\n"
                f"{e(s['summary'])}\n<i>↳ {e(s['why_it_matters'])}</i>"
            )
        blocks.append("\n\n".join(lines))
    if dashboard_url:
        blocks.append(f"\n<a href=\"{e(dashboard_url, quote=True)}\">Open dashboard →</a>")

    # Pack blocks into messages under the length limit
    messages, current = [], ""
    for block in blocks:
        if current and len(current) + len(block) + 2 > MAX_LEN:
            messages.append(current)
            current = ""
        current += ("\n\n" if current else "") + block
    if current:
        messages.append(current)
    return messages


def send(digest: dict) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.info("Telegram not configured — skipping send")
        return

    for text in render(digest, os.environ.get("DASHBOARD_URL")):
        body = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Telegram send failed: HTTP {resp.status}")
    log.info("Sent digest to Telegram")
