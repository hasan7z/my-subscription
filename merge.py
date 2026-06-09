import requests

INDEX_REPO = "AvenCores/goida-vpn-configs"

def get_all_repos():
    url = f"https://api.github.com/repos/{INDEX_REPO}/contents"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []

        items = r.json()

        repos = []

        for i in items:
            if i.get("type") == "dir":
                repos.append(i["name"])

        return repos

    except:
        return []

def get_files(repo):
    url = f"https://api.github.com/repos/{INDEX_REPO}/{repo}/contents"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def fetch(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None

def is_valid(text):
    if not text:
        return False

    t = text.lower()

    if "<html" in t:
        return False

    keywords = ["vmess", "vless", "trojan", "ss://", "ssr://"]

    return any(k in t for k in keywords)

def main():
    repos = get_all_repos()

    results = []
    seen = set()

    for repo in repos:
        items = get_files(repo)

        for item in items:
            if item.get("type") != "file":
                continue

            url = item.get("download_url")
            if not url:
                continue

            content = fetch(url)

            if is_valid(content):
                if content not in seen:
                    seen.add(content)
                    results.append(content)

    with open("all.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print("Done:", len(results))

if __name__ == "__main__":
    main()
