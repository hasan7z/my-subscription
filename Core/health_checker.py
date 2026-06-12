import json, os, time, socket, re, base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from Core.logger import log
DB_FILE, HEALTH_FILE, WORKERS, TIMEOUT, CHUNK = "database/database.json", "database/config_health.json", 50, 4, 3000
def extract_addr_port(cfg):
    try:
        cfg = cfg.strip()
        if cfg.startswith("vmess://"):
            data = json.loads(base64.b64decode(cfg[8:]).decode())
            return data.get("add"), data.get("port")
        for p in ["vless://", "trojan://", "ss://", "hy2://", "hysteria://", "tuic://"]:
            if cfg.startswith(p):
                m = re.search(rf"{re.escape(p)}[^@]+@([^:]+):(\\d+)", cfg)
                if m: return m.group(1), m.group(2)
        if cfg.startswith("ssr://"):
            dec = base64.b64decode(cfg[6:]).decode()
            parts = dec.split(":")
            if len(parts) >= 2: return parts[0], parts[1]
    except: pass
    return None, None
def worker(args):
    h, info = args
    addr, port = extract_addr_port(info.get("config", ""))
    if not addr or not port: return h, False, 0, "no_addr_port"
    try:
        t0 = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((addr, int(port)))
        sock.close()
        ms = (time.time() - t0) * 1000
        return h, True, ms, "open"
    except socket.timeout: return h, False, 0, "timeout"
    except ConnectionRefusedError: return h, False, 0, "refused"
    except Exception as e: return h, False, 0, str(e)
def main():
    if not os.path.exists(DB_FILE): return log("DB not found")
    with open(DB_FILE, "r", encoding="utf-8") as f: db = json.load(f)
    cutoff = datetime.now() - timedelta(hours=24)
    untested = [(h, i) for h, i in db.items() if not i.get("last_test") or datetime.fromisoformat(i.get("last_test")) < cutoff]
    targets = untested[:CHUNK]
    log(f"Testing {len(targets)} configs (Dynamic TCP, parallel={WORKERS})...")
    ok_cnt, fail_cnt, avg_ms = 0, 0, 0.0
    health_db = json.load(open(HEALTH_FILE, "r", encoding="utf-8")) if os.path.exists(HEALTH_FILE) else {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for f in as_completed({ex.submit(worker, t): t[0] for t in targets}):
            h, ok, ms, err = f.result()
            now = datetime.now().isoformat()
            db[h]["last_test"] = now
            entry = health_db.get(h, {"success": 0, "fail": 0, "history": [], "last_test": None})
            entry["last_test"] = now
            if ok:
                ok_cnt += 1
                avg_ms += ms
                entry["success"] += 1
                entry["history"].append(ms)
                if len(entry["history"]) > 30: entry["history"] = entry["history"][-30:]
            else:
                fail_cnt += 1
                entry["fail"] += 1
                entry["history"].append(9999)
                if len(entry["history"]) > 30: entry["history"] = entry["history"][-30:]
            health_db[h] = entry
    if ok_cnt: avg_ms /= ok_cnt
    log(f"Done: {ok_cnt} OK, {fail_cnt} FAIL. Avg: {avg_ms:.1f}ms")
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=2, ensure_ascii=False)
    with open(HEALTH_FILE, "w", encoding="utf-8") as f: json.dump(health_db, f, indent=2, ensure_ascii=False)
if __name__ == "__main__": main()
