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


DB_FILE = "database/database.json"


def main():

    log("===== RUN START =====")

    # آماده سازی سورس ها
    clean()
    sources = merge()

    # بارگذاری دیتابیس
    db = load_db(DB_FILE)

    # دانلود
    raw = download_sources(sources)

    # کشف سورس های جدید
    added = process(raw)

    # اجرای Engine
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

    # بروزرسانی دیتابیس
    db, new_count, expired = update_db(
        db,
        final
    )

    save_db(
        DB_FILE,
        db
    )

    # خروجی اصلی
    export_all(
        final
    )

    # خروجی Best ها
    best_sets = build_best(
        db
    )

    export_best_sets(
        best_sets
    )

    # آمار
    save(
        len(sources),
        len(parsed),
        len(valid),
        len(final)
    )

    # لاگ
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
