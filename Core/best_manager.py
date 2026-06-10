BEST_LEVELS = [
    10,
    20,
    50,
    100,
    500,
    1000
]


def build_best(db):

    items = []

    for _, info in db.items():

        if "config" not in info:
            continue

        score = info.get(
            "score",
            0
        )

        items.append(
            (
                score,
                info["config"]
            )
        )

    items.sort(
        key=lambda x: x[0],
        reverse=True
    )

    result = {}

    for n in BEST_LEVELS:

        result[n] = [

            config

            for _, config in items[:n]

        ]

    return result
