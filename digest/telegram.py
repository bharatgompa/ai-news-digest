"""Send the digest to a Telegram chat."""

import html
import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)

MAX_LEN = 4000  # Telegram limit is 4096 chars per message
STARS = {5: "🔥", 4: "⭐", 3: "•", 2: "·", 1: "·"}
SECTION_ICONS = {
    "India": "🇮🇳 ", "World": "🌍 ", "Markets & Money": "💰 ", "IPOs": "📈 ", "AI": "🤖 ",
    "Tech & Engineering": "💻 ", "Tech Industry & Jobs": "🏢 ", "Cricket": "🏏 ", "Worth a Watch": "📺 ",
}


def render(digest: dict, dashboard_url: str | None) -> list[str]:
    e = html.escape
    blocks = [f"<b>🗞 Daily Digest — {e(digest['date'])}</b>\n<i>{e(digest['headline'])}</i>"]
    for section in digest["sections"]:
        # One block per story (section header on the first) so no block can exceed MAX_LEN
        for i, s in enumerate(section["stories"]):
            header = f"<b>{SECTION_ICONS.get(section['title'], '')}{e(section['title'])}</b>\n\n" if i == 0 else ""
            blocks.append(
                f"{header}{STARS.get(s['importance'], '•')} <a href=\"{e(s['url'], quote=True)}\">{e(s['title'])}</a>\n"
                f"{e(s['summary'])}\n<i>↳ {e(s['why_it_matters'])}</i>"
            )
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
