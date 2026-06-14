import os
import requests
import re
import hashlib
from Core.logger import log

# منابع گسترده‌تر و به‌روز شده
WARP_SOURCES = [
    "https://raw.githubusercontent.com/ircfspace/warpsub/main/export/warp",
    "https://raw.githubusercontent.com/azadi_az_inja_migzare/azadi_az_inja_migzare/main/warp.txt",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/merged/warp",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/warp.txt",
    "https://raw.githubusercontent.com/MhdiTahworworker/v2ray/main/sub/warp",
    "https://raw.githubusercontent.com/ArdaYGN/V2ray-Free-Config-Collector/main/sub/warp",
]

# منابع مخصوص Warp on Warp (برای شرایط بحرانی)
WOW_SOURCES = [
    "https://raw.githubusercontent.com/ircfspace/warpsub/main/export/warp-on-warp",
    "https://raw.githubusercontent.com/azadi_az_inja_migzare/azadi_az_inja_migzare/main/warp-pro.txt",
]

def fetch_and_extract(sources, protocol_name):
    """استخراج هوشمند کانفیگ‌ها از منابع"""
    log(f"🔍 Fetching {protocol_name} configs from {len(sources)} sources...")
    all_configs = []
    
    for url in sources:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                # استخراج warp:// و wireguard://
                warp_uris = re.findall(r'warp://[^\s\n]+', res.text)
                wg_uris = re.findall(r'wireguard://[^\s\n]+', res.text)
                
                # تمیزسازی
                raw_matches = warp_uris + wg_uris
                clean_matches = [match.strip() for match in raw_matches if match.strip()]
                
                all_configs.extend(clean_matches)
                log(f"  ✅ {url}: {len(clean_matches)} configs")
            else:
                log(f"  ⚠️ {url}: HTTP {res.status_code}")
        except Exception as e:
            log(f"  ❌ {url}: {e}")
    
    return all_configs

def validate_and_deduplicate(configs):
    """اعتبارسنجی و حذف تکراری‌ها"""
    unique_configs = []
    seen_hashes = set()
    
    for cfg in configs:
        # بررسی اعتبار: باید warp:// یا wireguard:// داشته باشد و @ هم داشته باشد
        if ('warp://' in cfg or 'wireguard://' in cfg) and '@' in cfg:
            cfg_hash = hashlib.sha256(cfg.encode('utf-8')).hexdigest()
            if cfg_hash not in seen_hashes:
                seen_hashes.add(cfg_hash)
                unique_configs.append(cfg)
    
    return unique_configs

def save_configs(configs, output_path, label):
    """ذخیره کانفیگ‌ها با تضمین خط جدید"""
    if configs:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for cfg in configs:
                f.write(cfg + "\n")
        log(f"✅ Generated {output_path} with {len(configs)} {label} configs.")
    else:
        log(f"⚠️ No valid {label} configs found.")
        if not os.path.exists(output_path):
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# No valid {label} configs found at this time.\n")

def generate_warp():
    """تولید فایل‌های Warp و Warp on Warp"""
    log("🌀 Starting Warp extraction...")
    
    # ۱. Warp معمولی
    warp_configs = fetch_and_extract(WARP_SOURCES, "Warp")
    warp_unique = validate_and_deduplicate(warp_configs)
    save_configs(warp_unique, "output/warp.txt", "Warp")
    
    # ۲. Warp on Warp (برای شرایط بحرانی)
    log("🔍 Fetching Warp-on-Warp configs...")
    wow_configs = fetch_and_extract(WOW_SOURCES, "Warp-on-Warp")
    wow_unique = validate_and_deduplicate(wow_configs)
    save_configs(wow_unique, "output/warp_on_warp.txt", "Warp-on-Warp")
    
    # ۳. گزارش نهایی
    total = len(warp_unique) + len(wow_unique)
    log(f"📊 Total: {len(warp_unique)} Warp + {len(wow_unique)} WoW = {total} configs")

if __name__ == "__main__":
    generate_warp()
