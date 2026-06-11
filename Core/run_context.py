from datetime import datetime


def create():

    return {

        "started": datetime.utcnow().isoformat(),

        "downloaded": 0,

        "parsed": 0,

        "validated": 0,

        "normalized": 0,

        "unique": 0,

        "new": 0,

        "expired": 0

    }
