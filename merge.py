import os
import json
from datetime import datetime

# --- modules (بدون core) ---
from downloader import download_sources
from parser import parse_sources
from validator import validate_configs
from normalizer import normalize
from deduplicator import deduplicate_configs
from database import load_db, update_db, save_db
from exporter import export_all
from logger import log


SOURCES_FILE = "sources/sources.txt"
DB_FILE = "database/database.json"
STATS_FILE = "stats/stats.json"


def load_sources():
    if not os.path.exists(SOURCES_FILE):
        return []

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


def save_stats(stats):
    os.makedirs("stats", exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def main():
    log("=== RUN START ===")

    sources = load_sources()
    db = load_db(DB_FILE)

    raw = download_sources(sources)
    parsed = parse_sources(raw)
    valid = validate_configs(parsed)
    normalized = normalize(valid)

    unique, removed_dup = deduplicate_configs(normalized, db)

    db, new_count, expired_count = update_db(db, unique)

    save_db(DB_FILE, db)

    export_all(unique)

    stats = {
        "sources_total": len(sources),
        "configs_found": len(valid),
        "duplicates_removed": removed_dup,
        "new_configs": new_count,
        "expired_removed": expired_count,
        "run_time": str(datetime.utcnow())
    }

    save_stats(stats)

    log("=== RUN END ===")


if __name__ == "__main__":
    main()
