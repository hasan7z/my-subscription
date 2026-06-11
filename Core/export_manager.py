import os


OUTPUT_DIR = "output"


def ensure():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )
