def get_tier(score):

    if score >= 900:
        return "S"

    if score >= 800:
        return "A"

    if score >= 650:
        return "B"

    if score >= 500:
        return "C"

    if score >= 300:
        return "D"

    return "X"
