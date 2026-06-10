from Core.github_paths import COMMON_PATHS


def build(owner, repo, branch="main"):

    urls = []

    for path in COMMON_PATHS:

        urls.append(

            f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

        )

    return urls
