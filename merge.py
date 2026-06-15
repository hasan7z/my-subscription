import os
import json
import hashlib
import requests
from datetime import datetime
from Core.logger import log

DB_FILE = "database/database.json"
SOURCES_FILE = "Sources/sources.txt"

def calculate_protocol_score(config_str):
    """امتیازدهی بر اساس پروتکل (اولویت با VLESS Reality و Trojan طلایی)"""
    cfg_lower = config_str.lower()
    score = 0
    
    # VLESS Reality = بالاترین امتیاز
    if cfg_lower.startswith('vless://') and 'security=reality' in cfg_lower:
        score += 100
        if 'flow=xtls-rprx-vision' in cfg_lower:
            score += 20
    
    # Trojan با TLS = امتیاز بالا
    elif cfg_lower.startswith('trojan://') and 'security=tls' in cfg_lower:
        score += 80
    
    # VMess با TLS = امتیاز متوسط
    elif cfg_lower.startswith('vmess://') and 'tls' in cfg_lower:
        score += 50
    
    # SNI های طلایی = امتیاز اضافی
    golden_sni = ['cloudflare.com', 'speedtest.net', 'tap.az', 'amazon.com', 
                  'microsoft.com', 'apple.com', 'google.com', 'linkedin.com']
    if any(sni in cfg_lower for sni in golden_sni):
        score += 30
    
    # پورت‌های طلایی = امتیاز اضافی
    if ':443?' in config_str or ':8443?' in config_str:
        score += 20
    
    return score
def save_database_safely(db, db_file="database/database.json"):
    """ذخیره دیتابیس با سیستم ایمنی ۴۸ مگابایتی"""
    
    json_string = json.dumps(db, ensure_ascii=False, indent=2)
    size_in_bytes = len(json_string.encode('utf-8'))
    size_in_mb = size_in_bytes / (1024 * 1024)
    
    MAX_ALLOWED_MB = 48.0
    log(f"📊 Database size: {size_in_mb:.2f}MB (Limit: {MAX_ALLOWED_MB}MB)")
    
    if size_in_mb > MAX_ALLOWED_MB:
        log(f"⚠️ CRITICAL: Database exceeds {MAX_ALLOWED_MB}MB!")
        log("🔄 Activating Smart Trim: Keeping only highest-quality configs...")
        
        db_list = [{"hash": k, **v} for k, v in db.items()]
        
        for item in db_list:
            config_str = item.get("config", "")
            success = item.get("success", 0)
            fail = item.get("fail", 0)
            total_tests = success + fail
            
            if total_tests > 0:
                success_rate = (success / total_tests) * 100
            else:
                success_rate = 50
            
            protocol_score = calculate_protocol_score(config_str)
            item['final_score'] = (success_rate * 0.6) + (protocol_score * 0.4)
        
        db_list.sort(key=lambda x: x['final_score'], reverse=True)
        
        SAFE_CONFIG_COUNT = 90000
        db_list = db_list[:SAFE_CONFIG_COUNT]
        
        db = {item["hash"]: {k: v for k, v in item.items() if k not in ["hash", "final_score"]} 
              for item in db_list}
        
        log(f"✅ Smart Trim Complete: Kept top {len(db)} configs")
        
        new_json_string = json.dumps(db, ensure_ascii=False, indent=2)
        new_size_mb = len(new_json_string.encode('utf-8')) / (1024 * 1024)
        log(f"📉 New size: {new_size_mb:.2f}MB")
    
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    
    final_size = os.path.getsize(db_file) / (1024 * 1024)
    log(f"💾 Database saved: {final_size:.2f}MB")
def merge_configs():
    log("=" * 60)
    log("🔄 STARTING CONFIG MERGE WITH DEDUPLICATION")
    log("=" * 60)
    
    if not os.path.exists(SOURCES_FILE):
        log(f"❌ ERROR: {SOURCES_FILE} not found!")
        return {}
    
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    log(f"📥 Found {len(sources)} sources")
    
    # بارگذاری دیتابیس قبلی (اگر وجود دارد)
    db = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            log(f"✅ Loaded existing database: {len(db)} configs")
        except:
            log("⚠️ Could not load existing database. Starting fresh.")
    
    total_found = 0
    new_count = 0
    duplicates_removed = 0
    
    for source_url in sources:
        log(f"📥 Fetching: {source_url}")
        try:
            response = requests.get(source_url, timeout=30)
            if response.status_code == 200:
                configs = [line.strip() for line in response.text.split('\n') if line.strip()]
                
                for config_str in configs:
                    if not config_str:
                        continue
                    
                    total_found += 1
                    
                    # ✅ حذف تکراری با SHA-256
                    cfg_hash = hashlib.sha256(config_str.encode('utf-8')).hexdigest()
                    
                    if cfg_hash in db:
                        duplicates_removed += 1
                        continue
                    
                    db[cfg_hash] = {
                        "config": config_str,
                        "success": 0,
                        "fail": 0,
                        "last_seen": datetime.now().strftime("%Y-%m-%d")
                    }
                    new_count += 1
                
                log(f"   ✅ Extracted {len(configs)} configs")
            else:
                log(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            log(f"   ❌ Error: {e}")
    
    log(f"📊 Merge Stats:")
    log(f"   ├ Total configs found: {total_found}")
    log(f"   ├ Duplicates removed: {duplicates_removed}")
    log(f"   ├ New configs added: {new_count}")
    log(f"   └ Total unique in DB: {len(db)}")
    # ✅ استفاده از تابع ایمنی به جای json.dump معمولی
    save_database_safely(db, DB_FILE)
    
    log("=" * 60)
    log("🔄 CONFIG MERGE COMPLETE")
    log("=" * 60)
    
    return db

if __name__ == "__main__":
    merge_configs()
