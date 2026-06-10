def valid_source(text):

    if not text:
        return False

    text = text.strip()

    if not (
        text.startswith("http://")
        or
        text.startswith("https://")
    ):
        return False

    keywords = [

        "raw",

        "subscription",

        "sub",

        ".txt",

        ".json"

    ]

    return any(
        k in text.lower()
        for k in keywords
    )
