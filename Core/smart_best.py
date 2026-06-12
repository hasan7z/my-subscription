import json, os
from Core.logger import log

def calc_hybrid_score(info):
    s = info.get("success", 0)
    f = info.get("fail", 0)
    hist = info.get("history", [])
    total = s + f
    
    if total == 0:
        return -1000.0
        
    base_score = (s / total) * 500
    
    recent_tests = hist[-5:] if len(hist) >= 5 else hist
    if recent_tests:
        recent_successes = sum(1 for x in recent_tests if x < 9000)
        recent_ratio = recent_successes / len(recent_tests)
        
        if recent_ratio >= 0.8:
            base_score += 100
        elif recent_ratio >= 0.6:
            base_score += 50
        elif recent_ratio <= 0.2:
            base_score -= 150
        else:
            base_score -= 50
            
    valid_pings = [x for x in hist if x < 9000]
    if valid_pings:
        recent_valid_pings = valid_pings[-10:]
        avg_ping = sum(recent_valid_pings) / len(recent_valid_pings)
        
        if avg_ping < 150:
            base_score += 150
        elif avg_ping < 300:
            base_score += 100
        elif avg_ping < 500:
            base_score += 50
            
    base_score += min(total, 10) * 5
    return round(max(0, base_score), 2)

def main():
    log("Loading DB...")
    with open("database/database.json", "r", encoding="utf-8") as f:
        db = json.load(f)
    
    log("Calculating HYBRID dynamic scores...")
    for h, info in db.items():
        db[h]["score"] = calc_hybrid_score(info)
    
    log("Sorting ALL configs by score (descending)...")
    sorted_cfgs = sorted(db.values(), key=lambda x: x.get("score", -1000), reverse=True)
    
    # ✅ مرحله حیاتی ۱: حذف جهانی تکراری‌ها (Global Deduplication)
    # این تضمین می‌کند که یک رشته کانفیگ، در کل پوشه output فقط یک بار ظاهر شود
    unique_sorted_cfgs = []
    seen_configs = set()
    
    for cfg in sorted_cfgs:
        config_str = cfg.get("config", "").strip()
        if config_str and config_str not in seen_configs and cfg.get("score", -1000) > 0:
            seen_configs.add(config_str)
            unique_sorted_cfgs.append(cfg)
            
    log(f"Total UNIQUE valid configs after deduplication: {len(unique_sorted_cfgs)}")
    
    os.makedirs("output", exist_ok=True)
    
    # ✅ مرحله حیاتی ۲: تقسیم‌بندی طبقاتی بدون همپوشانی (Tiered Slicing)
    # هر فایل فقط بازه خاص خود را می‌گیرد و هیچ تکراری با فایل‌های دیگر نخواهد داشت
    ranges = {
        10: (0, 10),          # رتبه ۱ تا ۱۰
        20: (10, 20),         # رتبه ۱۱ تا ۲۰
        50: (20, 50),         # رتبه ۲۱ تا ۵۰
        100: (50, 100),       # رتبه ۵۱ تا ۱۰۰
        500: (100, 500),      # رتبه ۱۰۱ تا ۵۰۰
        1000: (500, 1000),    # رتبه ۵۰۱ تا ۱۰۰۰
        2500: (1000, 2500),   # رتبه ۱۰۰۱ تا ۲۵۰۰
        5000: (2500, 5000)    # رتبه ۲۵۰۱ تا ۵۰۰۰
    }
    
    for limit, (start, end) in ranges.items():
        path = f"output/Best{limit}.txt"
        
        # برش دقیق آرایه یکتا
        selected = unique_sorted_cfgs[start:end]
        
        with open(path, "w", encoding="utf-8") as f:
            for cfg in selected:
                f.write(cfg.get("config", "") + "\n")
        
        min_score = selected[-1].get("score", -1000) if selected else -1000
        log(f"✅ Wrote {path} ({len(selected)} UNIQUE configs, Rank {start+1} to {end}. Min score: {min_score})")
    
    log("✅ ALL Best files generated: ZERO duplicates across ALL files, Tiered perfectly!")

if __name__ == "__main__":
    main()
