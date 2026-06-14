import os
import hashlib
from Core.logger import log

# پیکربندی: فایل مرجع -> پیشوند فایل خروجی
ROTATION_CONFIG = {
    "output/best_vless.txt": "vless",
    "output/best_trojan.txt": "trojan",
    "output/best_vmess.txt": "vmess",
    "output/best_reality.txt": "reality",
    "output/best_iran.txt": "iran",
}

CHUNK_SIZE = 2500
MAX_FILES = 3  # ساخت حداکثر ۳ فایل برای هر پروتکل (مجموعاً ۷۵۰۰ کانفیگ متنوع)
STATE_DIR = "database/rotation_states"

def rotate_protocol(source_path, prefix):
    if not os.path.exists(source_path):
        log(f"⚠️ Source not found: {source_path}")
        return False

    # ۱. خواندن و حذف تکراری‌ها با اثر انگشت SHA-256
    with open(source_path, "r", encoding="utf-8") as f:
        all_configs = [line.strip() for line in f if line.strip()]

    unique_configs = []
    seen_hashes = set()
    for cfg in all_configs:
        cfg_hash = hashlib.sha256(cfg.encode('utf-8')).hexdigest()
        if cfg_hash not in seen_hashes:
            seen_hashes.add(cfg_hash)
            unique_configs.append(cfg)

    total = len(unique_configs)
    if total == 0:
        log(f"⚠️ No configs in {source_path}")
        return False

    # ۲. خواندن ایندکس سراسری این پروتکل
    state_file = os.path.join(STATE_DIR, f"{prefix}_index.txt")
    os.makedirs(STATE_DIR, exist_ok=True)
    
    current_index = 0
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                current_index = int(f.read().strip())
        except:
            current_index = 0

    # ۳. تولید تا ۳ فایل مجزا
    files_created = 0
    for file_num in range(1, MAX_FILES + 1):
        start_idx = (current_index + (file_num - 1) * CHUNK_SIZE) % total
        
        # مدیریت چرخش اگر به انتهای لیست رسیدیم
        if start_idx + CHUNK_SIZE > total:
            # ترکیب انتهای لیست با ابتدای لیست برای پر کردن ۲۵۰۰ تایی
            part1 = unique_configs[start_idx:]
            remaining = CHUNK_SIZE - len(part1)
            part2 = unique_configs[:remaining]
            selected = part1 + part2
        else:
            selected = unique_configs[start_idx : start_idx + CHUNK_SIZE]

        if not selected:
            break

        # ۴. ذخیره فایل
        output_path = f"output/{prefix}_{file_num}.txt"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for cfg in selected:
                f.write(cfg + "\n")
        
        files_created += 1
        log(f"✅ Generated {output_path} ({len(selected)} configs)")

    # ۵. به‌روزرسانی ایندکس سراسری (جلو رفتن به اندازه یک CHUNK برای دور بعدی)
    next_index = (current_index + CHUNK_SIZE) % total
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(str(next_index))

    log(f"🔄 {prefix} rotation complete: {files_created} files created. Next index: {next_index}")
    return True

def rotate_all():
    log("🚀 Starting Multi-File Universal Rotation...")
    success_count = 0
    for source, prefix in ROTATION_CONFIG.items():
        if rotate_protocol(source, prefix):
            success_count += 1
    log(f"✅ Multi-File Rotation completed: {success_count}/{len(ROTATION_CONFIG)} protocols processed.")

if __name__ == "__main__":
    rotate_all()
