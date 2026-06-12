import json
import os

FILE = "database/config_health.json"


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
