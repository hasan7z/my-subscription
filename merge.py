import requests

# repo اصلی لیست (همونی که دادی)
MAIN_REPO_API = "https://api.github.com/repos/AvenCores/goida-vpn-configs/contents"

def get_repo_items():
    try:
        r = requests.get(MAIN_REPO_API, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def get_raw_url(item):
    # فقط فایل‌ها مهمن نه فولدرها
    if item["type"] == "file":
        return item["download_url"]
    return None

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

    # حذف HTML
    if "<html" in t or "doctype html" in t:
        return False

    # حداقل طول
    if len(text) < 20:
        return False

    return True

def main():
    items = get_repo_items()

    results = []
    seen = set()

    for item in items:
        raw = get_raw_url(item)
        if not raw:
            continue

        content = fetch(raw)

        if is_valid(content):
            if content not in seen:
                seen.add(content)
                results.append(content)

    with open("all.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"Done: {len(results)} configs")

if __name__ == "__main__":
    main()
