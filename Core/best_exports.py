from Core.settings import BEST_EXPORTS


def build(cache):

    outputs = {}

    for n in BEST_EXPORTS:

        outputs[n] = [

            item["config"]

            for item in cache[:n]

        ]

    return outputs
