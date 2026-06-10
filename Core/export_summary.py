import json
import os
from datetime import datetime
from Core.protocol_detector import detect


FILE = "stats/export_summary.json"


def generate(configs):

    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total": len(configs),
        "protocols": {}
    }

    for c in configs:

        p = detect(c)

        if p not in data["protocols"]:
            data["protocols"][p] = 0

        data["protocols"][p] += 1

    os.makedirs("stats", exist_ok=True)

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

    return data
