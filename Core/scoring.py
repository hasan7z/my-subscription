from statistics import median


def calculate(info):

    success = info.get("success", 0)

    fail = info.get("fail", 0)

    history = info.get("history", [])

    total = success + fail

    if total == 0:
        return 0

    rate = success / total

    score = 0

    # Success Rate (500 امتیاز)

    score += rate * 500

    # Ping (300 امتیاز)

    if history:

        m = median(history)

        if m <= 50:

            score += 300

        elif m <= 100:

            score += 260

        elif m <= 150:

            score += 220

        elif m <= 250:

            score += 170

        elif m <= 400:

            score += 100

        else:

            score += 30

    # تجربه تست (200 امتیاز)

    score += min(total, 20) * 10

    return int(score)
