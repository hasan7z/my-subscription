import os
import json
import re
import random
import base64
from Core.logger import log

DB_FILE = "database/database.json"
OUTPUT_FILE = "output/jojo_style.txt"

# SNI های طلایی (امتیاز مثبت، نه فیلتر سخت)
GOLDEN_SNI = [
    'cloudflare.com', 'speedtest.net', 'tap.az', 'amazon.com',
    'microsoft.com', 'apple.com', 'google.com', 'linkedin.com',
    'vk-cdnvideo.com', 'mizulina.top', 'myfymain.com', 'cdnjst.org',
    'speed.cloudflare.com', 'discord.com', 'nginx.com', 'datadoghq.com'
]

# پورت‌های طلایی (امتیاز مثبت، نه فیلتر سخت)
GOLDEN_PORTS = [443, 8443, 2053, 2083, 2087, 2096, 8880, 8080, 2052, 2095]

def extract_server_ip(config_str):
    match = re.search(r'@([^:]+):', config_str)
    return match.group(1) if match else None

def calculate_jojo_score(config_str, success, fail):
    """امتیازدهی نرم بر اساس ویژگی‌های کانفیگ"""
    cfg_lower = config_str.lower()
    score = 0
    
    # ۱. امتیاز پایه بر اساس نرخ موفقیت (۰ تا ۱۰۰)
    total_tests = success + fail
    if total_tests > 0:
        score += (success / total_tests) * 100
    else:
        score += 60  # کانفیگ‌های تست‌نشده
    
    # ۲. امتیاز پروتکل
    if cfg_lower.startswith('vless://'):
        if 'security=reality' in cfg_lower:
            score += 30  # VLESS Reality = بهترین
            if 'flow=xtls-rprx-vision' in cfg_lower:
                score += 10
        elif 'security=tls' in cfg_lower:
            score += 20  # VLESS TLS
        else:
            score += 5
    elif cfg_lower.startswith('trojan://'):
        if 'security=tls' in cfg_lower:
            score += 15
    elif cfg_lower.startswith('vmess://'):
        if 'tls' in cfg_lower:
            score += 10
    elif cfg_lower.startswith('ss://'):
        score += 5
    
    # ۳. امتیاز SNI طلایی
    sni_match = re.search(r'sni=([^&]+)', cfg_lower)
    if sni_match:
        sni = sni_match.group(1)
        if any(golden_sni in sni for golden_sni in GOLDEN_SNI):
            score += 20
    
    # ۴. امتیاز پورت طلایی
    port_match = re.search(r':(\d+)[?/]', config_str)
    if port_match:
        port = int(port_match.group(1))
        if port in GOLDEN_PORTS:
            score += 10
    
    # ۵. امتیاز کشور
    if any(kw in cfg_lower for kw in ['de', '🇩🇪', 'germany', 'frankfurt']):
        score += 10
    elif any(kw in cfg_lower for kw in ['tr', '🇹🇷', 'turkey']):
        score += 8
    
    # ۶. حذف کانفیگ‌های ناامن
    if 'allowinsecure=1' in cfg_lower or 'allowinsecure=true' in cfg_lower:
        score -= 30
    
    return max(0, score)
def generate_jojo_style():
    log("=" * 60)
    log("🏆 STARTING JOJO STYLE (Smart Scoring Mode)")
    log("=" * 60)
    
    if not os.path.exists(DB_FILE):
        log(f"❌ ERROR: {DB_FILE} not found!")
        return
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    
    log(f"✅ Database loaded: {len(db)} total configs")
    
    scored_configs = []
    seen_servers = set()
    
    # ۱. امتیازدهی به همه کانفیگ‌ها
    for cfg_hash, info in db.items():
        config_str = info.get("config", "")
        if not config_str:
            continue
        
        # فقط پروتکل‌های معتبر
        cfg_lower = config_str.lower()
        if not (cfg_lower.startswith('vless://') or 
                cfg_lower.startswith('trojan://') or 
                cfg_lower.startswith('vmess://') or 
                cfg_lower.startswith('ss://')):
            continue
        
        success = info.get("success", 0)
        fail = info.get("fail", 0)
        
        # حذف کانفیگ‌های خیلی بد (کمتر از ۵۰٪ موفقیت)
        total_tests = success + fail
        if total_tests > 5 and (success / total_tests) < 0.5:
            continue
        
        # حذف تکراری‌های سرور
        server_ip = extract_server_ip(config_str)
        if server_ip and server_ip in seen_servers:
            continue
        
        # محاسبه امتیاز
        score = calculate_jojo_score(config_str, success, fail)
        
        scored_configs.append({
            "config": config_str,
            "score": score,            "server": server_ip
        })
        
        if server_ip:
            seen_servers.add(server_ip)
    
    # ۲. مرتب‌سازی بر اساس امتیاز
    scored_configs.sort(key=lambda x: x["score"], reverse=True)
    log(f"📊 Scored {len(scored_configs)} valid configs")
    
    # ۳. ✅ منطق شافل هوشمند
    POOL_SIZE = 150  # استخر ۱۵۰ تایی از بهترین‌ها
    CHUNK_SIZE = 30  # ۳۰ کانفیگ
    
    actual_pool_size = min(len(scored_configs), POOL_SIZE)
    top_pool = scored_configs[:actual_pool_size]
    
    # بر زدن تصادفی برای تغییر محتوا در هر آپدیت
    random.shuffle(top_pool)
    
    selected = top_pool[:CHUNK_SIZE]
    
    log(f"🔄 Smart Shuffle: Picked {len(selected)} fresh configs from top {actual_pool_size}")
    
    # ۴. ذخیره فایل نهایی
    if selected:
        os.makedirs("output", exist_ok=True)
        
        raw_text = "\n".join([item["config"] for item in selected])
        base64_encoded = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(base64_encoded)
        
        log(f"✅ SUCCESS: Generated {OUTPUT_FILE} (Base64) with {len(selected)} FRESH configs")
        avg_score = sum(item['score'] for item in selected) / len(selected)
        log(f"   📊 Average score: {avg_score:.1f}")
        unique_servers = len(set(item['server'] for item in selected if item['server']))
        log(f"   📊 Unique servers: {unique_servers}")
    else:
        log("⚠️ WARNING: No configs selected")
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# No golden configs found at this time.\n")
    
    log("=" * 60)
    log("🏆 JOJO STYLE GENERATION COMPLETE")
    log("=" * 60)

if __name__ == "__main__":    generate_jojo_style()
