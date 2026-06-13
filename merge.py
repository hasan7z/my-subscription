import json, os, re, hashlib
from datetime import datetime
from Core.logger import log
from Core import source_guardian

DB_FILE = "database/database.json"
CACHE_FILE = "database/source_cache.json"
SOURCES_FILE = "Sources/sources.txt"
OUTPUT_DIR = "output"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def download_sources():
    import requests
    os.makedirs(os.path.dirname(SOURCES_FILE), exist_ok=True)
    if not os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE, 'w', encoding='utf-8') as f: f.write('')
        return {}
    
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    cache = load_cache()
    raw = {}
    
    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # ۱. ساخت اثر انگشت (Fingerprint) از محتوا
                content_hash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()
                
                # ۲. بررسی کش هوشمند
                if url in cache and cache[url] == content_hash:
                    log(f"⏭️ Skipped (Unchanged): {url}")
                    raw[url] = "" # خالی می‌گذاریم تا پارس نشود
                    continue
                
                # اگر تغییر کرده یا جدید است
                cache[url] = content_hash
                raw[url] = response.text
                log(f"✅ Downloaded (New/Updated): {url}")
            else:
                log(f"❌ Failed ({response.status_code}): {url}")
                raw[url] = ""
        except Exception as e:
            log(f"❌ Error downloading {url}: {e}")
            raw[url] = ""
            
    save_cache(cache)
    return raw

def parse_configs(content):
    if not content: return []
    return [line.strip() for line in content.split('\n') if line.strip() and any(line.startswith(p) for p in ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://'])]

def main():
    log("===== RUN START =====")
    source_guardian.clean_active_sources()
    
    log("Downloading sources (with Smart Cache)...")
    raw = download_sources()
    
    # کشف منابع جدید (فقط از محتوای جدید دانلود شده)
    new_sources_count = 0
    for url, content in raw.items():
        if content:
            # منطق ساده کشف لینک (می‌تواند بعداً پیشرفته‌تر شود)
            pass 

    source_guardian.clean_active_sources()
    
    log("Parsing configs...")
    all_configs = []
    for url, content in raw.items():
        if content:
            configs = parse_configs(content)
            all_configs.extend(configs)
            log(f"  {url}: {len(configs)} configs")
    
    log(f"[PARSE DONE] {len(all_configs)}")
    
    # ۳. حذف تکراری بر اساس اثر انگشت (Fingerprint Deduplication)
    unique_configs = []
    seen_fingerprints = set()
    for cfg in all_configs:
        fingerprint = hashlib.sha256(cfg.encode('utf-8')).hexdigest()
        if fingerprint not in seen_fingerprints:
            seen_fingerprints.add(fingerprint)
            unique_configs.append(cfg)
            
    log(f"[DEDUP] {len(unique_configs)} unique configs (Fingerprint verified)")
    
    # به‌روزرسانی دیتابیس
    log("Updating database...")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    else:
        db = {}
        
    new_count = 0
    for config in unique_configs:
        cfg_hash = hashlib.md5(config.encode()).hexdigest() # هش کوتاه برای کلید دیتابیس
        if cfg_hash not in db:
            db[cfg_hash] = {"config": config, "added": datetime.now().isoformat(), "last_test": None, "success": 0, "fail": 0, "history": []}
            new_count += 1
            
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    log(f"[DB] total={len(db)} new={new_count}")
    
    # خروجی اولیه
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/all.txt", 'w', encoding='utf-8') as f:
        for cfg in unique_configs: f.write(cfg + '\n')
    log(f"[EXPORT] {len(unique_configs)} configs")
    
    source_guardian.evaluate_sources({url: {"success": bool(content), "valid_count": len(parse_configs(content))} for url, content in raw.items()})
    source_guardian.clean_active_sources()
    
    log(f"[FINAL] {len(unique_configs)}")
    log("===== RUN END =====")

if __name__ == "__main__":
    main()
