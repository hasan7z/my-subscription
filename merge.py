import os
import json
from datetime import datetime

from core.downloader import download_sources
from core.parser import parse_sources
from core.validator import validate_configs
from core.deduplicator import deduplicate_configs
from core.database import load_db, update_db
from core.exporter import export_all
from core.logger import log


CONFIG_DIR = "config"
SOURCES_FILE = "sources/sources.txt"
DB_FILE = "database/database.json"
OUTPUT_DIR = "output"
STATS_FILE = "stats/stats.json"


def load_sources():
    if not os.path.exists(SOURCES_FILE):
        return []

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_stats(stats):
    os.makedirs("stats", exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def main():
    start_time = datetime.utcnow()

    log("=== RUN STARTED ===")

    sources = load_sources()
    log(f"Loaded sources: {len(sources)}")

    db = load_db(DB_FILE)

    raw_data = download_sources(sources)
    parsed = parse_sources(raw_data)
    valid = validate_configs(parsed)

    deduped, removed_duplicates = deduplicate_configs(valid, db)

    db, new_configs, expired = update_db(db, deduped)

    export_all(deduped, OUTPUT_DIR)

    stats = {
        "run_time": str(start_time),
        "sources_total": len(sources),
        "configs_found": len(valid),
        "duplicates_removed": removed_duplicates,
        "new_configs": new_configs,
        "expired_removed": expired,
    }

    save_stats(stats)

    log(f"Done. configs={len(deduped)}")
    log("=== RUN FINISHED ===")


if __name__ == "__main__":
    main()
