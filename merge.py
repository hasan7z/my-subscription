import requests

# اینجا لیست repo ها رو می‌گذاریم (بعداً اتوماتش می‌کنیم)
REPOS = [
    "AvenCores/goida-vpn-configs"
]

def get_repo_files(repo):
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

    # حذف HTML
    if "<html" in t or "doctype html" in t:
        return False

    # فیلتر اولیه کانفیگ‌ها (v2ray / sub / base64 / json)
    keywords = ["vmess", "vless", "trojan", "ss://", "ssr://"]

    if any(k in text for k in keywords):
        return True

    # اگر خیلی کوتاه یا بی‌معنی بود
    if len(text) < 30:
        return False

    return True

def main():
    results = []
    seen = set()

    for repo in REPOS:
        items = get_repo_files(repo)

        for item in items:
            if item.get("type") != "file":
                continue

            download_url = item.get("download_url")
            if not download_url:
                continue

            content = fetch(download_url)

            if is_config(content):
                if content not in seen:
                    seen.add(content)
                    results.append(content)

    with open("all.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"Done: {len(results)} configs")

if __name__ == "__main__":
    main()
