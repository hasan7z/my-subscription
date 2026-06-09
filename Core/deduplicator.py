import hashlib
from core.logger import log


def make_hash(config: str) -> str:
    return hashlib.sha256(config.encode("utf-8")).hexdigest()


def deduplicate_configs(configs, db):
    """
    configs: list of valid configs
    db: database dict

    خروجی:
    - لیست یکتا
    - تعداد حذف شده
    """

    seen = set()
    unique = []
    removed = 0

    for c in configs:
        h = make_hash(c)

        # اگر قبلاً در دیتابیس بوده
        if h in db:
            db[h]["last_seen"] = db[h].get("last_seen")
            continue

        # تکراری در همین اجرا
        if h in seen:
            removed += 1
            continue

        seen.add(h)
        unique.append(c)

    log(f"[DEDUP] removed={removed} unique={len(unique)}")

    return unique, removed
