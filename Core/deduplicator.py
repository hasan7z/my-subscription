import hashlib
from Core.logger import log


def make_hash(config):
    return hashlib.sha256(
        config.encode("utf-8")
    ).hexdigest()


def deduplicate_configs(configs, db):

    seen = set()

    unique = []

    removed = 0

    for c in configs:

        h = make_hash(c)

        if h in seen:
            removed += 1
            continue

        seen.add(h)

        unique.append(c)

    log(
        f"[DEDUP] removed={removed} unique={len(unique)}"
    )

    return unique, removed
