NOTIFIERS = []


def register(func):

    NOTIFIERS.append(func)


def run(context=None):

    for func in NOTIFIERS:

        try:

            func(context)

        except Exception:

            pass
