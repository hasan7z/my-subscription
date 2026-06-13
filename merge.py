import json, os, re, hashlib
from datetime import datetime
import requests
from Core.logger import log
from Core import source_guardian
from Core import github_discovery
from Core import iran_optimizer
from Core import notifier

DB_FILE = "database/database.json"
CACHE_FILE = "database/source_cache.json"
SOURCES_FILE = "Sources/sources.txt"
OUTPUT_DIR = "output"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def download_sources():
    os.makedirs(os.path.dirname(SOURCES_FILE), exist_ok=True)
    if not os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        return {}
    
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    cache = load_cache()
    raw = {}
    
    for url in urls:
        # ✅ حلقه تلاش مجدد (Retry Logic)
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    content_hash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()
                    
                    if url in cache and cache[url] == content_hash:
                        log(f"⏭️ Skipped (Unchanged): {url}")
                        raw[url] = "" 
                    else:
                        cache[url] = content_hash
                        raw[url] = response.text
                        log(f"✅ Downloaded (New/Updated): {url}")
                    break # اگر موفق شد، از حلقه خارج شو
                else:
                    log(f"❌ Failed ({response.status_code}): {url}")
                    raw[url] = ""
                    break
            except Exception as e:
                if attempt < 2:
                    log(f"⚠️ Retry {attempt + 1}/2 for {url} due to: {e}")
                    time.sleep(2) # ۲ ثانیه صبر کن و دوباره تلاش کن
                else:
                    log(f"❌ Final Error downloading {url}: {e}")
                    raw[url] = ""
            
    save_cache(cache)
    return raw

def parse_configs(content):
    if not content:
        return []
    # فقط خطوطی که با پروتکل‌های معتبر شروع می‌شوند
    return [
        line.strip() for line in content.split('\n') 
        if line.strip() and any(line.startswith(p) for p in ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://'])
    ]

def main():
    log("===== RUN START =====")
    
    # ۱. پاکسازی اولیه منابع (حذف لینک‌های خراب از sources.txt)
    source_guardian.clean_active_sources()
    
    # ۲. ویژگی ۱: کشف خودکار منابع جدید از گیت‌هاب (قبل از دانلود)
    log("Running Auto-Discovery for new GitHub sources...")
    github_discovery.discover_new_sources()
    
    # ۳. دانلود منابع با کش هوشمند
    log("Downloading sources (with Smart Cache)...")
    raw = download_sources()
    
    # ۴. پاکسازی ثانویه (بعد از اضافه شدن منابع جدید)
    source_guardian.clean_active_sources()
    
    # ۵. پارس کردن کانفیگ‌ها
    log("Parsing configs...")
    all_configs = []
    for url, content in raw.items():
        if content:  # فقط اگر محتوا دانلود شده باشد (کش نشده باشد)
            configs = parse_configs(content)
            all_configs.extend(configs)
            if configs:
                log(f"  {url}: {len(configs)} configs")
    
    log(f"[PARSE DONE] {len(all_configs)}")
    
    # ۶. حذف تکراری بر اساس اثر انگشت (Fingerprint Deduplication)
    unique_configs = []
    seen_fingerprints = set()
    for cfg in all_configs:
        fp = hashlib.sha256(cfg.encode('utf-8')).hexdigest()
        if fp not in seen_fingerprints:
            seen_fingerprints.add(fp)
            unique_configs.append(cfg)
            
    log(f"[DEDUP] {len(unique_configs)} unique configs (Fingerprint verified)")
    
    # ۷. به‌روزرسانی دیتابیس
    log("Updating database...")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {}
        
    new_count = 0
    for config in unique_configs:
        # استفاده از MD5 برای کلید دیتابیس (سریع‌تر و کوتاه‌تر از SHA256 برای کلید)
        cfg_hash = hashlib.md5(config.encode()).hexdigest()
        if cfg_hash not in db:
            db[cfg_hash] = {
                "config": config, 
                "added": datetime.now().isoformat(), 
                "last_test": None, 
                "success": 0, 
                "fail": 0, 
                "history": []
            }
            new_count += 1
            
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    log(f"[DB] total={len(db)} new={new_count}")
    
    # ۸. ویژگی ۲: فیلتر پیشرفته مخصوص ایران
    log("Applying Iran-Optimized filter...")
    iran_optimized = iran_optimizer.filter_iran_optimized(unique_configs)
    if iran_optimized:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(f"{OUTPUT_DIR}/best_iran.txt", 'w', encoding='utf-8') as f:
            for cfg in iran_optimized:
                f.write(cfg + '\n')
        log(f"✅ Generated best_iran.txt ({len(iran_optimized)} configs)")
    
    # ۹. خروجی کلی (توسط .gitignore از کامیت شدن جلوگیری می‌شود)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/all.txt", 'w', encoding='utf-8') as f:
        for cfg in unique_configs:
            f.write(cfg + '\n')
    log(f"[EXPORT] {len(unique_configs)} configs to all.txt")
    
    # ۱۰. ارزیابی سلامت منابع
    source_results = {}
    for url, content in raw.items():
        valid_count = len(parse_configs(content))
        source_results[url] = {
            "success": bool(content) and valid_count > 0, 
            "valid_count": valid_count
        }
    source_guardian.evaluate_sources(source_results)
    
    # ۱۱. پاکسازی نهایی منابع
    source_guardian.clean_active_sources()
    
    # ۱۲. ویژگی ۳: سیستم اعلان و بررسی سلامت
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        sources_count = len([line for line in f if line.strip() and not line.startswith('#')])
    
    notifier.check_health(db, sources_count, new_count)
    
    log(f"[FINAL] {len(unique_configs)}")
    log(f"[NEW] {new_count}")
    log("===== RUN END =====")

if __name__ == "__main__":
    main()
