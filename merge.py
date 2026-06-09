import requests

REPOS = ["AvenCores/goida-vpn-configs"]

def get_all_files(repo):
    url = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        return []

    return r.json().get("tree", [])

def fetch(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

def extract_configs(text):
    if not text:
        return []

    lines = text.splitlines()
    configs = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # حذف HTML
        if "<html" in line.lower():
            continue

        # فقط خطوط کانفیگ
        if any(k in line for k in ["vmess", "vless", "trojan", "ss://", "ssr://"]):
            configs.append(line)

    return configs

def main():
    results = []
    seen = set()

    for repo in REPOS:
        files = get_all_files(repo)

        for f in files:
            if f.get("type") != "blob":
                continue

            path = f.get("path", "")

            # فقط فایل‌های قابل استفاده
            if not any(ext in path for ext in [".txt", ".sub", ".json", ".yaml", ".md", ""]):
                continue

            raw_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"

            content = fetch(raw_url)

            configs = extract_configs(content)

            for c in configs:
                if c not in seen:
                    seen.add(c)
                    results.append(c)

    with open("all.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"Done: {len(results)} configs")

if __name__ == "__main__":
    main()
