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

from Core.exporter import (
    export_all,
    export_best_sets
)

from Core.best_manager import (
    build_best
)

from Core.final_stats import save

from Core.logger import log

from Core.health_manager import (
    load as load_health,
    save as save_health,
    update as update_health
)


DB_FILE = "database/database.json"


def main():

    log("===== RUN START =====")

    clean()

    sources = merge()

    db = load_db(
        DB_FILE
    )

    health = load_health()

    raw = download_sources(
        sources
    )

    added = process(
        raw
    )

    result = execute(
        raw,
        db
    )

    parsed = result.get(
        "parsed",
        []
    )

    valid = result.get(
        "valid",
        []
    )

    final = result.get(
        "final",
        []
    )

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

    best_sets = build_best(
        db
    )

    export_best_sets(
        best_sets
    )

    for url, content in raw.items():

        ok = bool(content)

        count = 0

        if content:

            count = content.count(
                "\n"
            ) + 1

        health = update_health(
            url,
            ok,
            count,
            health
        )

    save_health(
        health
    )

    save(
        len(sources),
        len(parsed),
        len(valid),
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

    log(
        "===== RUN END ====="
    )


if __name__ == "__main__":
    main()
