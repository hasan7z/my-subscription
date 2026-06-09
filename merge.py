import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.downloader import download_sources
from core.parser import parse_sources
from core.validator import validate_configs
from core.normalizer import normalize
from core.deduplicator import deduplicate_configs
from core.database import load_db, update_db, save_db
from core.exporter import export_all
from core.logger import log

import os
import json


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
        "expired_removed": expired_count
    }

    save_stats(stats)

    log("=== RUN END ===")


if __name__ == "__main__":
    main()
