from datetime import datetime


def update_history(info):

    history = info.get(
        "history",
        []
    )

    history.append(
        datetime.utcnow().isoformat()
    )

    info["history"] = history[-20:]

    return info
