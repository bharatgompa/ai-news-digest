"""Entry point: python -m digest [--no-send] [--dry-run]

  --dry-run   fetch feeds and print what would be sent to Claude; no API calls
  --no-send   build and save the digest but don't message Telegram
"""

import argparse
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import fetch, summarize, telegram

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data"
IST = timezone(timedelta(hours=5, minutes=30))

log = logging.getLogger("digest")


def save(digest: dict) -> Path:
    (DATA / "digests").mkdir(parents=True, exist_ok=True)
    path = DATA / "digests" / f"{digest['date']}.json"
    path.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")

    # index.json lists available dates (newest first) for the dashboard
    index_path = DATA / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    index = [e for e in index if e["date"] != digest["date"]]
    stories = sum(len(s["stories"]) for s in digest["sections"])
    index.append({"date": digest["date"], "headline": digest["headline"], "stories": stories})
    index.sort(key=lambda e: e["date"], reverse=True)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-send", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    items, failed = fetch.collect(config)
    log.info("Collected %d unique items (%d sources failed)", len(items), len(failed))

    if args.dry_run:
        for it in items:
            print(f"[{it.id}] {it.source}: {it.title}")
        return
    if not items:
        raise SystemExit("No items collected — check feeds/network")

    digest = summarize.summarize(items, config["interests"], config["settings"]["digest_size"])
    digest.update(
        date=datetime.now(IST).strftime("%Y-%m-%d"),
        generated_at=int(time.time()),
        items_scanned=len(items),
        failed_sources=failed,
    )

    log.info("Saved %s", save(digest))
    if not args.no_send:
        telegram.send(digest)


if __name__ == "__main__":
    main()
