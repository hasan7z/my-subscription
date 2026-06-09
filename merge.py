import requests
from bs4 import BeautifulSoup

# صفحه‌ای که ۲۶ repo داخلشه
INDEX_URL = "https://github.com/AvenCores/goida-vpn-configs"

def get_repos():
    try:
        r = requests.get(INDEX_URL, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        repos = set()

        for a in soup.find_all("a"):
            href = a.get("href")
            if href and "/tree/main" in href:
                full = "https://github.com" + href
                repo_name = full.replace("https://github.com/", "").replace("/tree/main", "")
                repos.add(repo_name)

        return list(repos)

    except:
        return []

def get_files(repo):
    url = f"https://api.github.com/repos/{repo}/contents"
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

def is_config(text):
    if not text:
        return False

    t = text.lower()

    if "<html" in t or "doctype html" in t:
        return False

    keywords = ["vmess", "vless", "trojan", "ss://", "ssr://"]

    return any(k in t for k in keywords)

def main():
    repos = get_repos()

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

            if is_config(content):
                if content not in seen:
                    seen.add(content)
                    results.append(content)

    with open("all.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"Done: {len(results)} configs")

if __name__ == "__main__":
    main()
