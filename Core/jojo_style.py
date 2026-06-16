import os
import json
import re
import random
import base64
from Core.logger import log

DB_FILE = "database/database.json"
OUTPUT_FILE = "output/jojo_style.txt"

GOLDEN_SNI = [
    'cloudflare.com', 'speedtest.net', 'tap.az', 'amazon.com',
    'microsoft.com', 'apple.com', 'google.com', 'linkedin.com',
    'vk-cdnvideo.com', 'mizulina.top', 'myfymain.com', 'cdnjst.org',
    'speed.cloudflare.com', 'discord.com', 'nginx.com', 'datadoghq.com'
]

GOLDEN_PORTS = [443, 8443, 2053, 2083, 2087, 2096, 8880, 8080, 2052, 2095, 80, 8080]

def extract_server_ip(config_str):
    match = re.search(r'@([^:]+):', config_str)
    return match.group(1) if match else None

def calculate_flat_score(config_str, success, fail):
    """امتیازدهی تخت با فاکتور شانس برای ایجاد تنوع ۵۰-۵۰"""
    cfg_lower = config_str.lower()
    score = 0
    
    # ۱. امتیاز پایه موفقیت (فشرده‌شده: حداکثر ۴۰ امتیاز)
    total_tests = success + fail
    if total_tests > 0:
        score += (success / total_tests) * 40
    else:
        score += 25  # کانفیگ‌های جدید شانس دارند
    
    # ۲. امتیاز پروتکل (کوچک و برابر: حداکثر ۱۰ امتیاز)
    if cfg_lower.startswith('vless://'):
        score += 10 if 'security=reality' in cfg_lower else 5
    elif cfg_lower.startswith('trojan://'):
        score += 8 if 'security=tls' in cfg_lower else 4
    elif cfg_lower.startswith('vmess://') or cfg_lower.startswith('ss://'):
        score += 5
    
    # ۳. امتیاز SNI و پورت (هر کدام ۵ امتیاز)
    sni_match = re.search(r'sni=([^&]+)', cfg_lower)
    if sni_match and any(s in sni_match.group(1) for s in GOLDEN_SNI):
        score += 5
        
    port_match = re.search(r':(\d+)[?/]', config_str)
    if port_match and int(port_match.group(1)) in GOLDEN_PORTS:
        score += 5
    
    # ۴. 🎲 فاکتور شانس تصادفی (۰ تا ۳۰ امتیاز)
    # این خط باعث می‌شود کانفیگ‌های با امتیاز نزدیک، هر بار جایگاه متفاوتی داشته باشند
    score += random.uniform(0, 30)
    
    # ۵. جریمه کانفیگ‌های ناامن
    if 'allowinsecure=1' in cfg_lower or 'allowinsecure=true' in cfg_lower:
        score -= 20
    
    return max(0, score)
def generate_jojo_style():
    log("=" * 60)
    log("🏆 STARTING JOJO STYLE (50/50 Chance Mode)")
    log("=" * 60)
    
    if not os.path.exists(DB_FILE):
        log(f"❌ ERROR: {DB_FILE} not found!")
        return
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    
    log(f"✅ Database loaded: {len(db)} total configs")
    
    scored_configs = []
    seen_servers = set()
    
    for cfg_hash, info in db.items():
        config_str = info.get("config", "")
        if not config_str:
            continue
        
        cfg_lower = config_str.lower()
        if not (cfg_lower.startswith('vless://') or cfg_lower.startswith('trojan://') or 
                cfg_lower.startswith('vmess://') or cfg_lower.startswith('ss://')):
            continue
        
        success = info.get("success", 0)
        fail = info.get("fail", 0)
        total_tests = success + fail
        
        # فقط کانفیگ‌هایی که واقعاً خراب هستند را حذف کن (زیر ۴۰٪ موفقیت با تست زیاد)
        if total_tests > 5 and (success / total_tests) < 0.4:
            continue
        
        server_ip = extract_server_ip(config_str)
        if server_ip and server_ip in seen_servers:
            continue
        
        score = calculate_flat_score(config_str, success, fail)
        
        scored_configs.append({
            "config": config_str,
            "score": score,
            "server": server_ip
        })
        
        if server_ip:
            seen_servers.add(server_ip)
    
    # مرتب‌سازی بر اساس امتیاز نهایی (که شامل شانس تصادفی است)
    scored_configs.sort(key=lambda x: x["score"], reverse=True)
    log(f"📊 Scored {len(scored_configs)} valid configs")
    
    # ✅ افزایش استخر به ۲۰۰ تا برای تنوع بیشتر
    POOL_SIZE = 200  
    CHUNK_SIZE = 30  
    
    actual_pool_size = min(len(scored_configs), POOL_SIZE)
    top_pool = scored_configs[:actual_pool_size]
    
    # بر زدن نهایی
    random.shuffle(top_pool)
    selected = top_pool[:CHUNK_SIZE]
    
    log(f"🔄 50/50 Shuffle: Picked {len(selected)} configs from top {actual_pool_size}")
    
    if selected:
        os.makedirs("output", exist_ok=True)
        raw_text = "\n".join([item["config"] for item in selected])
        base64_encoded = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(base64_encoded)
        
        log(f"✅ SUCCESS: Generated {OUTPUT_FILE} (Base64) with {len(selected)} configs")
        avg_score = sum(item['score'] for item in selected) / len(selected)
        log(f"   📊 Average score: {avg_score:.1f}")
    else:
        log("⚠️ WARNING: No configs selected")
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# No configs found.\n")
    
    log("=" * 60)
    log("🏆 JOJO STYLE GENERATION COMPLETE")
    log("=" * 60)

if __name__ == "__main__":
    generate_jojo_style()
