from Core.cleanup_filter import should_delete


def cleanup(db):

    removed = 0

    new_db = {}

    for h, info in db.items():

        if should_delete(info):

            removed += 1
            continue

        new_db[h] = info

    return new_db, removed
