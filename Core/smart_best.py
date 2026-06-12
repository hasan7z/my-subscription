import json, os
from Core.logger import log

def calc_score(info):
    s, f = info.get("success", 0), info.get("fail", 0)
    hist = info.get("history", [])
    total = s + f
    if total == 0:
        return -1000  # جریمه سنگین برای تست‌نشده‌ها
    score = (s / total) * 500
    valid_hist = [x for x in hist if x < 9000]
    if valid_hist:
        median = sorted(valid_hist)[len(valid_hist)//2]
        score += max(0, 300 - median)
    score += min(total, 20) * 10
    return round(score, 2)

def main():
    log("Loading DB...")
    with open("database/database.json", "r", encoding="utf-8") as f:
        db = json.load(f)
    log("Calculating scores...")
    for h, info in db.items():
        db[h]["score"] = calc_score(info)
    log("Sorting...")
    sorted_cfgs = sorted(db.values(), key=lambda x: (x.get("score", -1000), x.get("last_seen", "")), reverse=True)
    os.makedirs("output", exist_ok=True)
    for limit in [10, 20, 50, 100, 500, 1000]:
        path = f"output/Best{limit}.txt"
        count = 0
        with open(path, "w", encoding="utf-8") as f:
            for cfg in sorted_cfgs:
                if cfg.get("score", -1000) > 0:
                    f.write(cfg.get("config", "") + "\n")
                    count += 1
                    if count >= limit:
                        break
        log(f"✅ Wrote {path} ({count} working configs)")

if __name__ == "__main__":
    main()
