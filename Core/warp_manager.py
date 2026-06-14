import os
import requests
import re
import hashlib
from Core.logger import log

WARP_SOURCES = [
    "https://raw.githubusercontent.com/ircfspace/warpsub/main/export/warp",
    "https://raw.githubusercontent.com/azadi_az_inja_migzare/azadi_az_inja_migzare/main/warp.txt",
    "https://raw.githubusercontent.com/azadi_az_inja_migzare/azadi_az_inja_migzare/main/warp-pro.txt"
]

def generate_warp():
    log("🌀 Fetching and cleaning Warp configs...")
    all_configs = []
    
    for url in WARP_SOURCES:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                # ✅ استفاده از Regex برای استخراج تمیز کانفیگ‌ها
                # این خط هر چیزی که با warp:// شروع شود و تا فاصله یا انتهای خط ادامه یابد را جدا می‌کند
                warp_matches = re.findall(r'warp://[^\s\n]+', res.text)
                
                # همچنین خطوطی که فرمت wireguard دارند را هم چک می‌کنیم
                wg_matches = [line.strip() for line in res.text.split('\n') if 'reserved' in line.lower() or 'wg_port' in line.lower()]
                
                valid_lines = warp_matches + wg_matches
                
                # تمیزسازی نهایی: حذف فاصله‌های اضافی اول و آخر
                clean_lines = [line.strip() for line in valid_lines if line.strip()]
                
                all_configs.extend(clean_lines)
                log(f"✅ Extracted {len(clean_lines)} clean warp configs from {url}")
        except Exception as e:
            log(f"⚠️ Failed to fetch {url}: {e}")

    # حذف تکراری‌ها با اثر انگشت SHA-256
    unique_configs = []
    seen_hashes = set()
    for cfg in all_configs:
        cfg_hash = hashlib.sha256(cfg.encode('utf-8')).hexdigest()
        if cfg_hash not in seen_hashes:
            seen_hashes.add(cfg_hash)
            unique_configs.append(cfg)

    # ✅ ذخیره با تضمین خط جدید (\n) برای هر کانفیگ
    if unique_configs:
        os.makedirs("output", exist_ok=True)
        with open("output/warp.txt", "w", encoding="
