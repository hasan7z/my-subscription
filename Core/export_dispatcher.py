from Core.export_context import build
from Core.export_pipeline import run


def dispatch(

    files,

    stats

):

    context = build(

        files,

        stats

    )

    run(context)
