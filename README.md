# AI News Digest

A personal AI agent that reads ~20 news sources and YouTube channels every morning, uses Claude to pick
the ~15 stories that actually matter to me, and delivers them to **Telegram** plus a **day-wise dashboard**
hosted free on GitHub Pages.

Built twice: a **Python** version (runs on GitHub Actions) and an **n8n** low-code version.

```
 RSS feeds ─┐                                      ┌─► Telegram message
 YouTube  ──┼─► fetch & dedupe ─► Claude (filter, ─┤
 HN       ──┘   (last 26h)        rank, summarise) └─► docs/data/*.json ─► GitHub Pages dashboard
                                   structured JSON
```

## Design decisions (good interview talking points)

- **Structured outputs, not free text.** Claude returns JSON validated against a schema
  (`output_config.format`), so parsing never breaks on formatting drift.
- **Never trust the model with links.** Claude returns only an `item_id`; real URLs are re-attached from
  the fetched data, so hallucinated or mangled links can't happen.
- **Prompt-injection aware.** Feed content is wrapped in tags and the system prompt treats it as data.
- **Fault tolerant.** A dead feed is logged and skipped; the digest records which sources failed.
- **Serverless & free.** GitHub Actions cron + git as the database + GitHub Pages as the frontend.
  The only cost is the Claude API: about $3/month on Sonnet 5.5, about $1/month on Haiku 4.5.
- **Refusal fallback.** `fallbacks: "default"` re-runs a declined request on a fallback model server-side.

## Project layout

```
sources.yaml                 # feeds, YouTube channels, your interest profile, limits  ← edit this
digest/                      # Python agent: fetch.py → summarize.py → telegram.py
docs/index.html              # dashboard (static, reads docs/data/*.json)
.github/workflows/           # daily cron at 06:47 IST
n8n/                         # n8n version (import ai-news-digest.workflow.json)
```

---

## Setup — Python version (~30 min)

### 1. Get the keys

| What | Where |
|---|---|
| **Anthropic API key** | console.anthropic.com → Billing → buy $5 of credit → API Keys. That's about 1.5 months on Sonnet, or about 5 months on Haiku. |
| **Telegram bot token** | In Telegram, message **@BotFather** → `/newbot` → copy the token. |
| **Your Telegram chat ID** | Send any message to your new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `message.chat.id`. |

### 2. Push to GitHub

Create a new repo on **your personal GitHub** (public is needed for free GitHub Pages; keys stay secret
either way), then:

```bash
git remote add origin https://github.com/<you>/ai-news-digest.git
git push -u origin main
```

### 3. Add secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**:
`ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

### 4. Turn on the dashboard

Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch `main`, folder **`/docs`** → Save.
Your dashboard: `https://<you>.github.io/ai-news-digest/`

### 5. First run

Repo → **Actions → Daily digest → Run workflow**. In ~1 minute you get a Telegram message and the
dashboard shows today's digest. After that it runs by itself every morning at 06:47 IST.

> GitHub may delay scheduled runs by some minutes at busy times, and disables cron on repos with no
> activity for 60 days — the daily digest commit keeps it active.

### Run locally (optional)

```bash
pip install -r requirements.txt
python -m digest --dry-run     # just fetch and list items, no API calls
export ANTHROPIC_API_KEY=...    # PowerShell: $env:ANTHROPIC_API_KEY="..."
python -m digest --no-send      # build + save digest, skip Telegram
```

---

## Setup — n8n version (~1 hour)

1. **Run n8n** — easiest: n8n Cloud free trial (n8n.io). Self-host free with Docker:
   `docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n` → open `localhost:5678`.
   (Self-hosted only runs while your machine is on.)
2. **Import** — Workflows → *Import from File* → `n8n/ai-news-digest.workflow.json`.
3. **Claude credential** — open the *Claude* node → Credential → *Header Auth* → Name `x-api-key`,
   Value = your Anthropic key.
4. **Telegram credential** — open *Send to Telegram* → create a Telegram credential with the bot token,
   and replace `YOUR_CHAT_ID` with your chat ID.
5. Click **Test workflow**. When it works, toggle the workflow **Active**.

To change feeds or the prompt, edit the Code nodes directly in n8n (or edit `n8n/code/*.js` and re-run
`powershell -File n8n/build-workflow.ps1` to regenerate the JSON).

---

## Customising

- **Add your YouTube channels** in `sources.yaml` → `youtube_channels` (instructions for finding the
  channel ID are at the top of the file).
- **Change what you care about** — edit `interests` in `sources.yaml`. This is the most important knob.
- **Model** — defaults to `claude-sonnet-5-5`. Set the `DIGEST_MODEL` env var in the workflow to
  `claude-opus-5-5` for higher quality at ~2× the cost.

## Ideas for v2

- Fetch YouTube **transcripts** so videos are summarised from what's said, not just titles.
- **Reply to the bot** to ask follow-up questions about a story (Telegram webhook + Claude with history).
- A weekly "what mattered this week" roll-up from the saved JSONs.
- Thumbs up/down on stories in the dashboard → feed preferences back into the prompt.
