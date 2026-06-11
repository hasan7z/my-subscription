import json
import os

PATH = "database/graveyard.json"


def load():

    if not os.path.exists(PATH):
        return {}

    try:

        with open(
            PATH,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f).get(
                "items",
                {}
            )

    except:

        return {}


def save(items):

    os.makedirs(
        "database",
        exist_ok=True
    )

    with open(
        PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "items": items
            },
            f,
            indent=2,
            ensure_ascii=False
        )
