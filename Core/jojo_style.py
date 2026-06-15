import os
import json
import base64
import re
from Core.logger import log

DB_FILE = "database/database.json"
OUTPUT_FILE = "output/jojo_style.txt"

# فیلترهای سخت‌گیرانه به سبک MahsaNG
GOLDEN_SNI = [
    'cloudflare.com', 'speedtest.net', 'tap.az', 'amazon.com', 
    'microsoft.com', 'apple.com', 'google.com', 'linkedin.com',
    'vk-cdnvideo.com', 'cdn.discordapp.com'
]

GOLDEN_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

def is_golden_config(config_str):
    """بررسی اینکه آیا کانفیگ استانداردهای طلایی MahsaNG را دارد"""
    cfg_lower = config_str.lower()
    
    # 1. فقط VLESS یا VMess (MahsaNG از هر دو استفاده می‌کند)
    if not (cfg_lower.startswith('vless://') or cfg_lower.startswith('vmess://')):
        return False
    
    # 2. فقط TLS یا Reality (نه ناامن)
    if 'security=tls' not in cfg_lower and 'security=reality' not in cfg_lower:
        return False
    
    # 3. فقط پورت‌های طلایی
    port_match = re.search(r':(\d+)[?/]', config_str)
    if port_match:
        port = int(port_match.group(1))
        if port not in GOLDEN_PORTS:
            return False
    
    # 4. فقط SNI های طلایی
    sni_match = re.search(r'sni=([^&]+)', cfg_lower)
    if sni_match:
        sni = sni_match.group(1)
        if not any(golden_sni in sni for golden_sni in GOLDEN_SNI):
            return False
    
    # 5. Fingerprint مرورگر
    if 'fp=chrome' not in cfg_lower and 'fp=firefox' not in cfg_lower and 'fp=random' not in cfg_lower:
        return False
    
    # 6. حذف کانفیگ‌های ناامن
    if 'allowinsecure=1' in cfg_lower or 'allowinsecure=true' in cfg_lower:        return False
    
    return True

def extract_server_ip(config_str):
    """استخراج IP سرور برای حذف تکراری‌های سرور"""
    match = re.search(r'@([^:]+):', config_str)
    if match:
        return match.group(1)
    return None

def generate_jojo_style():
    """تولید 30 کانفیگ طلایی به سبک MahsaNG (Base64)"""
    log("🏆 Generating JoJo Style (30 Golden Configs - MahsaNG Pattern)...")
    
    if not os.path.exists(DB_FILE):
        log("⚠️ database.json not found. Skipping.")
        return
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    
    # 1. فیلتر کردن کانفیگ‌های طلایی
    golden_configs = []
    seen_servers = set()
    
    for cfg_hash, info in db.items():
        config_str = info.get("config", "")
        if not config_str:
            continue
        
        # بررسی استانداردهای طلایی
        if not is_golden_config(config_str):
            continue
        
        # بررسی سلامت
        success = info.get("success", 0)
        fail = info.get("fail", 0)
        total_tests = success + fail
        
        if total_tests > 0:
            success_rate = success / total_tests
            if success_rate < 0.8:
                continue
        
        # حذف تکراری‌های سرور
        server_ip = extract_server_ip(config_str)
        if server_ip and server_ip in seen_servers:
            continue
                # امتیازدهی
        score = 0
        if total_tests > 0:
            score += (success / total_tests) * 100
        else:
            score += 70
        
        cfg_lower = config_str.lower()
        if any(kw in cfg_lower for kw in ['de', '🇩🇪', 'germany', 'frankfurt']):
            score += 30
        elif any(kw in cfg_lower for kw in ['tr', '🇹🇷', 'turkey']):
            score += 25
        elif any(kw in cfg_lower for kw in ['ae', '🇦🇪', 'uae']):
            score += 20
        
        golden_configs.append({
            "config": config_str,
            "score": score,
            "server": server_ip
        })
        
        if server_ip:
            seen_servers.add(server_ip)
    
    # 2. مرتب‌سازی بر اساس امتیاز
    golden_configs.sort(key=lambda x: x["score"], reverse=True)
    
    # 3. انتخاب 30 تای برتر
    top_30 = golden_configs[:30]
    
    # 4. ✅ ذخیره به صورت Base64 (مثل MahsaNG!)
    if top_30:
        os.makedirs("output", exist_ok=True)
        
        # تبدیل به متن ساده
        raw_text = "\n".join([item["config"] for item in top_30])
        
        # کدگذاری Base64
        base64_encoded = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(base64_encoded)
        
        log(f"✅ Generated {OUTPUT_FILE} with {len(top_30)} golden configs (Base64 - MahsaNG style)")
        
        servers = set(item["server"] for item in top_30 if item["server"])
        log(f"   📊 Unique servers: {len(servers)}")
        log(f"   📊 Average score: {sum(item['score'] for item in top_30) / len(top_30):.1f}")
    else:
        log("⚠️ No golden configs found matching MahsaNG standards")
if __name__ == "__main__":
    generate_jojo_style()
