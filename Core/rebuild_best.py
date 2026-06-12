import json
from Core.best_manager import build_best
from Core.exporter import export_best_sets
from Core.logger import log
def main():
    try:
        with open("database/database.json", "r", encoding="utf-8") as f: db = json.load(f)
        best_sets = build_best(db)
        export_best_sets(best_sets)
        log("✅ Rebuild SUCCESS")
    except Exception as e:
        log(f"❌ Rebuild ERROR: {e}")
if __name__ == "__main__": main()
