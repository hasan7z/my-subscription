import os
from Core.logger import log


OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "all.txt")


def export_all(configs):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        for item in configs:
            f.write(item.strip())
            f.write("\n")

    log(
        f"[EXPORT] {len(configs)} configs -> {OUTPUT_FILE}"
    )
