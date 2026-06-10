from Core.source_cleaner import clean
from Core.source_merger import merge

from Core.downloader import download_sources
from Core.auto_source_manager import process

from Core.engine import execute

from Core.database import (
    load_db,
    update_db,
    save_db
)

from Core.exporter import export_all

from Core.final_stats import save

from Core.logger import log


DB_FILE = "database/database.json"


def main():

    log("===== RUN START =====")

    clean()

    sources = merge()

    db = load_db(DB_FILE)

    raw = download_sources(sources)

    added = process(raw)

    result = execute(raw, db)

    final = result["final"]

    db, new_count, expired = update_db(
        db,
        final
    )

    save_db(
        DB_FILE,
        db
    )

    export_all(
        final
    )

    save(
        len(sources),
        len(result["parsed"]),
        len(result["valid"]),
        len(final)
    )

    log(
        f"[AUTO SOURCE] {added}"
    )

    log(
        f"[FINAL] {len(final)}"
    )

    log(
        f"[NEW] {new_count}"
    )

    log(
        f"[EXPIRED] {expired}"
    )

    log("===== RUN END =====")


if __name__ == "__main__":
    main()
