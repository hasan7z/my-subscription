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
    
    # ✅ مرحله ۱: حذف جهانی تکراری‌ها (فقط یک بار انجام می‌شود)
    unique_sorted_cfgs = []
    seen_configs = set()
    
    for cfg in sorted_cfgs:
        config_str = cfg.get("config", "").strip()
        # فقط کانفیگ‌هایی که امتیاز مثبت دارند و تکراری نیستند
        if config_str and config_str not in seen_configs and cfg.get("score", -1000) > 0:
            seen_configs.add(config_str)
            unique_sorted_cfgs.append(cfg)
            
    total_unique = len(unique_sorted_cfgs)
    log(f"Total UNIQUE valid configs available: {total_unique}")
    
    os.makedirs("output", exist_ok=True)
    
    # ✅ مرحله ۲: برش تجمعی (Cumulative Slicing)
    # فایل Best50 دقیقاً ۵۰ تای اول را می‌گیرد، Best100 دقیقاً ۱۰۰ تای اول را، و الی آخر
    limits = [10, 20, 50, 100, 500, 1000, 2500, 5000]
    
    for limit in limits:
        path = f"output/Best{limit}.txt"
        
        # برش از اول لیست تا 'limit'
        # اگر تعداد کانفیگ‌های سالم کمتر از limit باشد، تا همان تعداد پر می‌شود (خطا نمی‌دهد)
        selected = unique_sorted_cfgs[:limit]
        
        with open(path, "w", encoding="utf-8") as f:
            for cfg in selected:
                f.write(cfg.get("config", "") + "\n")
        
        min_score = selected[-1].get("score", 0) if selected else 0
        log(f"✅ Wrote {path} ({len(selected)} configs filled. Min score: {min_score})")
    
    log("✅ ALL Best files generated: Cumulative, Fully Populated, ZERO duplicates!")

if __name__ == "__main__":
    main()
