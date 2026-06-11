from Core.status import calculate_status
from Core.quarantine import move_to_quarantine


def process(db):

    changed = 0

    for h in db:

        info = db[h]

        status = calculate_status(info)

        if status == "weak":

            if info.get("status") != "quarantine":

                db[h] = move_to_quarantine(info)

                changed += 1

        else:

            info["status"] = status

    return db, changed
