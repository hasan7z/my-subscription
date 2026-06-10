from Core.protocol_detector import detect


def apply(configs):

    result = []

    for c in configs:

        if not c:
            continue

        c = c.strip()

        if detect(c) == "unknown":
            continue

        if len(c) < 10:
            continue

        result.append(c)

    return result
