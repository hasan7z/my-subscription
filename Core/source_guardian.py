import json, os, re
from datetime import datetime
from urllib.parse import urlparse
from Core.logger import log

HEALTH_FILE = "database/sources_health.json"
BLACKLIST_FILE = "database/source_blacklist.txt"
ACTIVE_SOURCES_FILE = "Sources/sources.txt"
MAX_SOURCES_LIMIT = 50  # 🚨 محدودیت سخت: حداکثر ۵۰ لینک در فایل سورس

def normalize_url(url):
    url = url.strip().rstrip("/")
    url = re.sub(r'github\.com/([^/]+/[^/]+)/blob/(.+)', r'raw.githubusercontent.com/\1/\2', url)
    url = re.sub(r'cdn\.jsdelivr\.net/gh/([^/]+/[^/]+)@(.+)', r'raw.githubusercontent.com/\1/\2', url)
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def load_health():
    if not os.path.exists(HEALTH_FILE): return {}
    try:
        with open(HEALTH_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_health(data):
    os.makedirs("database", exist_ok=True)
    with open(HEALTH_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE): return set()
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f: return set(line.strip() for line in f if line.strip())

def save_blacklist(blacklist):
    os.makedirs("database", exist_ok=True)
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        for url in sorted(list(blacklist)): f.write(url + "\n")

def evaluate_sources(sources_results):
    health = load_health()
    blacklist = load_blacklist()
    now = datetime.now().isoformat()
    banned_count = 0
    
    for url, result in sources_results.items():
        norm_url = normalize_url(url)
        if norm_url in blacklist: continue
        if norm_url not in health:
            health[norm_url] = {"success": 0, "fail": 0, "last_check": None, "total_valid": 0}
            
        entry = health[norm_url]
        entry["last_check"] = now
        
        if result.get("success") and result.get("valid_count", 0) >= 5:
            entry["success"] += 1
            entry["fail"] = 0
            entry["total_valid"] += result.get("valid_count", 0)
        else:
            entry["fail"] += 1
            entry["success"] = 0
            
        if entry["fail"] >= 2: # 🚨 حساس‌تر شد: با ۲ بار شکست بن می‌شود
            blacklist.add(norm_url)
            if norm_url in health: del health[norm_url]
            banned_count += 1
            log(f"🚫 Blacklisted source (2 fails): {norm_url}")
            
    save_health(health)
    save_blacklist(blacklist)
    log(f"✅ Source Guardian: {banned_count} sources blacklisted.")

def clean_active_sources():
    if not os.path.exists(ACTIVE_SOURCES_FILE): return
    
    with open(ACTIVE_SOURCES_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    blacklist = load_blacklist()
    health = load_health()
    scored_sources = []
    
    for line in lines:
        norm_url = normalize_url(line)
        if norm_url and norm_url.startswith("http") and norm_url not in blacklist:
            # محاسبه امتیاز سلامت سورس
            h = health.get(norm_url, {"success": 0, "fail": 0})
            # فرمول امتیاز: هر موفقیت +۱۰، هر شکست -۲۰
            score = (h["success"] * 10) - (h["fail"] * 20)
            scored_sources.append((score, norm_url))
            
    # 🚨 مرتب‌سازی بر اساس امتیاز و نگهداری فقط ۵۰ تای برتر
    scored_sources.sort(key=lambda x: x[0], reverse=True)
    top_sources = [item[1] for item in scored_sources[:MAX_SOURCES_LIMIT]]
    
    with open(ACTIVE_SOURCES_FILE, "w", encoding="utf-8") as f:
        for url in top_sources:
            f.write(url + "\n")
            
    log(f"🧹 Sources trimmed: {len(lines)} -> {len(top_sources)} (Hard limit: {MAX_SOURCES_LIMIT})")
