import os
import sys
import json
from datetime import datetime

# =========================
# FIX PATH (حل کامل Core/core conflict)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "Core")

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, CORE_DIR)

# 🔥 مهم: alias برای حل مشکل core vs Core
import types
sys.modules["core"] = sys.modules.get("Core")

# =========================
# IMPORTS (همه یکدست با Core)
# =========================
from Core.downloader import download_sources
from Core.parser import parse_sources
from Core.validator import validate_configs
from Core.normalizer import normalize
from Core.deduplicator import deduplicate_configs
from Core.database import load_db, update_db, save_db
from Core.exporter import export_all
from Core.logger import log


# =========================
# PATHS
# =========================
SOURCES_FILE = "Sources/Sources.txt"
DB_FILE = "database/database.json"
STATS_FILE = "stats/stats.json"


# =========================
# LOAD SOURCES
# =========================
def load_sources():
    print("SOURCES_FILE =", SOURCES_FILE)
    print("EXISTS =", os.path.exists(SOURCES_FILE))

    if not os.path.exists(SOURCES_FILE):
        return []

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        data = [x.strip() for x in f if x.strip()]

    print("LINES =", len(data))

    return data


# =========================
# SAVE STATS
# =========================
def save_stats(stats):
    os.makedirs("stats", exist_ok=True)

    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


# =========================
# MAIN PIPELINE
# =========================
def main():
    log("=== RUN START ===")

    sources = load_sources()
    db = load_db(DB_FILE)

    raw = download_sources(sources)
    print("SOURCES =", len(sources))
    print("RAW =", len(raw))

    parsed = parse_sources(raw)
    print("PARSED =", len(parsed))

    valid = validate_configs(parsed)
    print("VALID =", len(valid))

    normalized = normalize(valid)
    print("NORMALIZED =", len(normalized))

    unique, removed_dup = deduplicate_configs(normalized, db)

    db, new_count, expired_count = update_db(db, unique)
    save_db(DB_FILE, db)

    export_all(normalized)

    stats = {
        "run_time": str(datetime.utcnow()),
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
