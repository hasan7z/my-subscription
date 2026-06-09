import requests
import re
import base64

INDEX_REPO = "AvenCores/goida-vpn-configs"

def get_repos():
    url = f"https://api.github.com/repos/{INDEX_REPO}/contents"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []
    return [i["name"] for i in r.json() if i["type"] == "dir"]

def get_readme(repo):
    url = f"https://raw.githubusercontent.com/{INDEX_REPO}/{repo}/main/README.md"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

def extract_links(text):
    return re.findall(r'https?://[^\s)"]+', text)

def fetch(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text.strip()
    except:
        pass
    return ""

def decode_base64(text):
    try:
        if len(text) > 50 and "=" in text:
            return base64.b64decode(text).decode("utf-8", errors="ignore")
    except:
        pass
    return text

def is_config(text):
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in ["vmess", "vless", "trojan", "ss://", "ssr://"])

def main():
    repos = get_repos()

    results = []
    seen = set()

    for repo in repos:
        readme = get_readme(repo)
        links = extract_links(readme)

        for link in links:
            content = fetch(link)
            content = decode_base64(content)

            if is_config(content):
                if content not in seen:
                    seen.add(content)
                    results.append(content)

    with open("all.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print("Done:", len(results))

if __name__ == "__main__":
    main()
