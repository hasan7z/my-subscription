import json
import os
import re
from datetime import datetime
from Core.logger import log
from Core import source_guardian

DB_FILE = "database/database.json"
SOURCES_FILE = "Sources/sources.txt"
OUTPUT_DIR = "output"

def download_sources():
    """دانلود منابع از sources.txt"""
    import requests
    
    if not os.path.exists(SOURCES_FILE):
        log("❌ sources.txt not found")
        return {}
    
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    raw = {}
    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                raw[url] = response.text
                log(f"✅ Downloaded: {url}")
            else:
                log(f"❌ Failed ({response.status_code}): {url}")
                raw[url] = ""
        except Exception as e:
            log(f"❌ Error downloading {url}: {e}")
            raw[url] = ""
    
    return raw

def parse_configs(content):
    """پارس کانفیگ‌ها از محتوا"""
    if not content:
        return []
    
    configs = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and any(line.startswith(p) for p in ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://']):
            configs.append(line)
    
    return configs

def load_db():
    """بارگذاری دیتابیس"""
    if not os.path.exists(DB_FILE):
        return {}
    
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    """ذخیره دیتابیس"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def update_db(db, new_configs):
    """به‌روزرسانی دیتابیس با کانفیگ‌های جدید"""
    import hashlib
    
    new_count = 0
    for config in new_configs:
        # ساخت هش برای کانفیگ
        config_hash = hashlib.md5(config.encode()).hexdigest()
        
        if config_hash not in db:
            db[config_hash] = {
                "config": config,
                "added": datetime.now().isoformat(),
                "last_test": None,
                "success": 0,
                "fail": 0,
                "history": []
            }
            new_count += 1
    
    return new_count

def export_configs(db):
    """خروجی گرفتن از کانفیگ‌ها"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # استخراج همه کانفیگ‌ها
    all_configs = [info["config"] for info in db.values()]
    
    # نوشتن در فایل
    with open(f"{OUTPUT_DIR}/all.txt", 'w', encoding='utf-8') as f:
        for config in all_configs:
            f.write(config + '\n')
    
    log(f"[EXPORT] {len(all_configs)} configs")
    return all_configs

def extract_urls_from_content(content):
    """استخراج لینک‌های جدید از محتوا"""
    if not content:
        return []
    
    url_pattern = r'https?://[^\s<>"\']+'
    urls = re.findall(url_pattern, content)
    
    valid_urls = []
    for url in urls:
        url = url.strip().rstrip('/')
        if any(bad in url.lower() for bad in ['telegram.me', 't.me/', 'youtube', 'twitter']):
            continue
        if any(good in url.lower() for good in ['raw.githubusercontent', 'jsdelivr', '.txt', '.json', '/sub/', 'github.com']):
            valid_urls.append(url)
    
    return list(set(valid_urls))

def auto_source_discovery(raw_content):
    """کشف خودکار منابع جدید"""
    if not os.path.exists(SOURCES_FILE):
        os.makedirs(os.path.dirname(SOURCES_FILE), exist_ok=True)
        with open(SOURCES_FILE, 'w', encoding='utf-8') as f:
            f.write('')
    
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        existing_urls = set(line.strip() for line in f if line.strip())
    
    new_urls = set()
    for url, content in raw_content.items():
        extracted = extract_urls_from_content(content)
        new_urls.update(extracted)
    
    urls_to_add = new_urls - existing_urls
    
    if urls_to_add:
        with open(SOURCES_FILE, 'a', encoding='utf-8') as f:
            for url in urls_to_add:
                f.write(url + '\n')
        log(f"[AUTO SOURCE] Added {len(urls_to_add)} new sources")
    
    return len(urls_to_add)

def main():
    log("===== RUN START =====")
    
    # ۱. پاکسازی منابع
    source_guardian.clean_active_sources()
    
    # ۲. دانلود منابع
    log("Downloading sources...")
    raw = download_sources()
    
    # ۳. کشف منابع جدید
    added = auto_source_discovery(raw)
    
    # ۴. پاکسازی ثانویه
    source_guardian.clean_active_sources()
    
    # ۵. پارس کانفیگ‌ها
    log("Parsing configs...")
    all_configs = []
    for url, content in raw.items():
        configs = parse_configs(content)
        all_configs.extend(configs)
        log(f"  {url}: {len(configs)} configs")
    
    log(f"[PARSE DONE] {len(all_configs)}")
    
    # ۶. حذف تکراری‌ها
    unique_configs = list(set(all_configs))
    log(f"[DEDUP] {len(unique_configs)} unique configs")
    
    # ۷. به‌روزرسانی دیتابیس
    log("Updating database...")
    db = load_db()
    new_count = update_db(db, unique_configs)
    save_db(db)
    log(f"[DB] total={len(db)} new={new_count}")
    
    # ۸. خروجی
    log("Exporting configs...")
    export_configs(db)
    
    # ۹. ارزیابی سلامت منابع
    source_results = {}
    for url, content in raw.items():
        ok = bool(content)
        count = len(parse_configs(content))
        source_results[url] = {"success": ok, "valid_count": count}
    
    source_guardian.evaluate_sources(source_results)
    
    # ۱۰. پاکسازی نهایی
    source_guardian.clean_active_sources()
    
    log(f"[FINAL] {len(unique_configs)}")
    log(f"[NEW] {new_count}")
    log("===== RUN END =====")

if __name__ == "__main__":
    main()
