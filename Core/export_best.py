import os


OUTPUT = "output"


def write(name, configs):

    os.makedirs(
        OUTPUT,
        exist_ok=True
    )

    path = os.path.join(
        OUTPUT,
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
