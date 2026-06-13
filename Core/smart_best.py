import json, os, base64, urllib.parse, re
from Core.logger import log

def is_cloudflare(cfg):
    """شناسایی هوشمند کانفیگ‌های پشت کلادفلیر"""
    cfg_lower = cfg.lower()
    cf_ips = ['104.', '172.64.', '172.67.', '188.114.', '104.16.', '104.18.', '104.21.']
    if any(ip in cfg_lower for ip in cf_ips): return True
    if 'cloudflare' in cfg_lower or 'cdn-cgi' in cfg_lower or 'workers.dev' in cfg_lower: return True
    
    # بررسی SNI یا Host
    try:
        if cfg_lower.startswith("vless://") or cfg_lower.startswith("vmess://"):
            # استخراج ساده هاست برای بررسی
            match = re.search(r'@([^:]+):\d+', cfg_lower)
            if match and any(ip in match.group(1) for ip in cf_ips): return True
    except: pass
    return False

def get_country_boost(info):
    cfg = info.get("config", "").lower()
    search_text = cfg
    if cfg.startswith("vmess://"):
        try:
            b64 = cfg[8:] + "=" * ((4 - len(cfg[8:]) % 4) % 4)
            data = json.loads(base64.b64decode(b64).decode("utf-8", errors="ignore"))
            search_text += " " + str(data.get("ps", "")).lower()
        except: pass
    try: search_text += " " + urllib.parse.unquote(cfg).lower()
    except: pass

    tier_1 = ['ae', 'tr', 'fi', 'de', '🇦🇪', '🇹🇷', '🇫🇮', '🇩🇪', 'dubai', 'istanbul', 'frankfurt', 'امارات', 'ترکیه', 'فنلاند', 'آلمان']
    for c in tier_1:
        if c in search_text: return 300
    tier_2 = ['nl', 'fr', 'gb', 'ch', '🇳🇱', '🇫🇷', '🇬🇧', '🇨🇭', 'amsterdam', 'paris', 'london', 'هلند', 'فرانسه', 'انگلیس']
    for c in tier_2:
        if c in search_text: return 200
    tier_3 = ['us', 'ca', 'jp', 'sg', '🇺🇸', '🇨🇦', '🇯🇵', '🇸🇬', 'آمریکا', 'کانادا', 'ژاپن']
    for c in tier_3:
        if c in search_text: return 100
    return 0

def calc_final_score(info):
    s, f = info.get("success", 0), info.get("fail", 0)
    total = s + f
    base = 200 if total == 0 else (s / total) * 500
    hist = info.get("history", [])
    if hist and hist[-1] == 9999: base *= 0.7
    return round(max(0, base + get_country_boost(info)), 2)

def main():
    log("Loading DB...")
    with open("database/database.json", "r", encoding="utf-8") as f:
        db = json.load(f)
    
    log("Calculating Country-Boosted scores...")
    for h, info in db.items():
        info["final_score"] = calc_final_score(info)
        
    sorted_all = sorted(db.values(), key=lambda x: x.get("final_score", 0), reverse=True)
    
    unique_configs = []
    seen_fingerprints = set()
    for cfg in sorted_all:
        cfg_str = cfg.get("config", "").strip()
        if cfg_str:
            fp = hashlib.sha256(cfg_str.encode('utf-8')).hexdigest() # اثر انگشت نهایی
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                unique_configs.append(cfg)
            
    log(f"Total unique configs (Fingerprint verified): {len(unique_configs)}")
    os.makedirs("output", exist_ok=True)
    
    # ۱. فایل‌های استاندارد
    limits = [10, 20, 50, 100, 500, 1000, 2500, 5000]
    pos = 0
    for limit in limits:
        path = f"output/Best{limit}.txt"
        selected = unique_configs[pos:pos + limit]
        with open(path, "w", encoding="utf-8") as f:
            for cfg in selected: f.write(cfg.get("config", "") + "\n")
        pos += limit

    # ۲. فایل ویژه best_i.txt
    with open("output/best_i.txt", "w", encoding="utf-8") as f:
        for cfg in unique_configs[:100]: f.write(cfg.get("config", "") + "\n")

    # ۳. ✨ تفکیک پروتکل و کلادفلیر
    protocols = {"vless": [], "vmess": [], "trojan": [], "reality": [], "shadowsocks": []}
    cloudflare_configs = []
    
    for cfg in unique_configs:
        cfg_str = cfg.get("config", "").lower()
        
        # بررسی کلادفلیر
        if is_cloudflare(cfg_str):
            cloudflare_configs.append(cfg.get("config", ""))
            
        # بررسی پروتکل
        if "security=reality" in cfg_str or "reality" in cfg_str: protocols["reality"].append(cfg.get("config", ""))
        elif cfg_str.startswith("vless://"): protocols["vless"].append(cfg.get("config", ""))
        elif cfg_str.startswith("trojan://"): protocols["trojan"].append(cfg.get("config", ""))
        elif cfg_str.startswith("vmess://"): protocols["vmess"].append(cfg.get("config", ""))
        elif cfg_str.startswith("ss://") or cfg_str.startswith("ssr://"): protocols["shadowsocks"].append(cfg.get("config", ""))
            
    for proto, configs in protocols.items():
        if configs:
            with open(f"output/best_{proto}.txt", "w", encoding="utf-8") as f:
                for c in configs: f.write(c + "\n")
            log(f"✅ Wrote {len(configs)} {proto.upper()} configs")
            
    if cloudflare_configs:
        with open("output/best_cloudflare.txt", "w", encoding="utf-8") as f:
            for c in cloudflare_configs: f.write(c + "\n")
        log(f"✅ Wrote {len(cloudflare_configs)} CLOUDFLARE optimized configs")

    # ۴. خروجی Base64 (فقط ۱۰۰۰ کانفیگ برتر برای جلوگیری از حجم بالا)
    top_1000 = unique_configs[:1000]
    base64_str = "\n".join([cfg.get("config", "") for cfg in top_1000])
    with open("output/subscription_base64.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode(base64_str.encode('utf-8')).decode('utf-8'))
    log(f"✅ Generated subscription_base64.txt (Top 1000 configs)")

if __name__ == "__main__":
    import hashlib # اضافه شده برای اثر انگشت
    main()
