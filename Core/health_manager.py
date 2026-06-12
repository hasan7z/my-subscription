import json
import os

FILE = "database/source_health.json"


def load():

    if not os.path.exists(FILE):
        return {}

    try:

        with open(
            FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return {}


def save(data):

    os.makedirs(
        "database",
        exist_ok=True
    )

    with open(
        FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


def update(
    url,
    success,
    count,
    db
):

    item = db.get(
        url,
        {}
    )

    item["success"] = item.get(
        "success",
        0
    )

    item["failed"] = item.get(
        "failed",
        0
    )

    item["runs"] = item.get(
        "runs",
        0
    )

    item["last_configs"] = item.get(
        "last_configs",
        0
    )

    item["runs"] += 1

    if success:

        item["success"] += 1
        item["last_configs"] = count

    else:

        item["failed"] += 1

    total = (
        item["success"]
        +
        item["failed"]
    )

    if total == 0:

        item["rate"] = 0

    else:

        item["rate"] = round(
            item["success"]
            * 100
            / total,
            2
        )

    db[url] = item

    return db
