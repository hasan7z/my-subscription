from Core.logger import log


def check(configs):

    good = []
    bad = 0

    for c in configs:

        if not c:
            bad += 1
            continue

        c = c.strip()

        if len(c) < 10:
            bad += 1
            continue

        good.append(c)

    log(
        f"[INTEGRITY] good={len(good)} bad={bad}"
    )

    return good
