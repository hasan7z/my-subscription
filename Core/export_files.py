import os


def list_files(
    directory="output"
):

    result = []

    if not os.path.exists(
        directory
    ):
        return result

    for name in sorted(
        os.listdir(directory)
    ):

        path = os.path.join(
            directory,
            name
        )

        if os.path.isfile(path):

            result.append(path)

    return result
