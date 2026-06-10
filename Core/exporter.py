import os
from Core.logger import log


OUTPUT_DIR = "output"
ALL_FILE = os.path.join(OUTPUT_DIR, "all.txt")
ARCHIVE_FILE = os.path.join(OUTPUT_DIR, "archive.txt")


def export_all(configs):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # خروجی آخرین اجرا
    with open(
        ALL_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("\n".join(configs))

    # آرشیو دائمی
    archive = set()

    if os.path.exists(ARCHIVE_FILE):

        with open(
            ARCHIVE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            archive = set(
                x.strip()
                for x in f
                if x.strip()
            )

    archive.update(configs)

    archive = sorted(archive)

    with open(
        ARCHIVE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("\n".join(archive))

    log(
        f"[EXPORT] all={len(configs)} archive={len(archive)}"
    )
def export_best(configs, name="Best100.txt"):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    path = os.path.join(
        OUTPUT_DIR,
        name
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n".join(configs)
        )

    log(
        f"[BEST EXPORT] {name} total={len(configs)}"
    )
def export_best_sets(best_sets):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    for n, configs in best_sets.items():

        path = os.path.join(

            OUTPUT_DIR,

            f"Best{n}.txt"

        )

        with open(

            path,

            "w",

            encoding="utf-8"

        ) as f:

            f.write(

                "\n".join(configs)

            )

        log(

            f"[BEST {n}] {len(configs)}"

        )
