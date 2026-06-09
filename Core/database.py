import json
import os
from datetime import datetime
from Core.logger import log


def load_db(path):
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_db(path, db):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def update_db(db, configs):
    """
    آپدیت دیتابیس با کانفیگ‌های جدید
    """

    now = datetime.utcnow().isoformat()

    new_count = 0
    expired_count = 0

    for c in configs:
        h = hashlib_sha(c)

        if h not in db:
            db[h] = {
                "first_seen": now,
                "last_seen": now,
                "miss_hours": 0,
                "sources": []
            }
            new_count += 1
        else:
            db[h]["last_seen"] = now
            db[h]["miss_hours"] = 0

    # expire logic (فعلاً ساده، بعداً 56h دقیق می‌کنیم)
    to_delete = []

    for h, data in db.items():
        if "miss_hours" not in data:
            data["miss_hours"] = 0

        data["miss_hours"] += 12

        if data["miss_hours"] >= 56:
            to_delete.append(h)

    for h in to_delete:
        del db[h]
        expired_count += 1

    log(f"[DB] new={new_count} expired={expired_count}")

    return db, new_count, expired_count


def hashlib_sha(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
