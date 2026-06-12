import json, os, time, socket, base64
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from Core.logger import log

DB_FILE = "database/database.json"
WORKERS, TIMEOUT, CHUNK = 50, 4, 3000

def extract_addr_port(cfg):
    try:
        cfg = cfg.strip()
        if cfg.startswith("vmess://"):
            b64 = cfg[8:] + "=" * ((4 - len(cfg[8:]) % 4) % 4)
            data = json.loads(base64.b64decode(b64).decode("utf-8", errors="ignore"))
            return str(data.get("add") or data.get("address")), str(data.get("port"))
        if "://" in cfg:
            p = urlparse(cfg)
            addr, port = p.hostname, p.port
            if not addr and "@" in p.netloc:
                parts = p.netloc.split("@")[-1].split(":")
                if len(parts) == 2:
                    addr, port = parts[0], parts[1]
            if addr and port:
                return str(addr), str(port)
    except:
        pass
    return None, None

def worker(args):
    h, info = args
    addr, port = extract_addr_port(info.get("config", ""))
    if not addr or not port:
        return h, False, 0
    try:
        t0 = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((addr, int(port)))
        sock.close()
        return h, True, (time.time() - t0) * 1000
    except:
        return h, False, 0

def main():
    if not os.path.exists(DB_FILE):
        return log("DB not found")
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    now = datetime.now()
    to_test = []
    for h, i in db.items():
        s, f_cnt = i.get("success", 0), i.get("fail", 0)
        last = i.get("last_test")
        if s == 0 and f_cnt > 5:
            if last and (now - datetime.fromisoformat(last)).days < 7:
                continue
        if not last or (now - datetime.fromisoformat(last)).total_seconds() > 86400 or (s == 0 and f_cnt == 0):
            to_test.append((h, i))
    targets = to_test[:CHUNK]
    log(f"Smart Filter: {len(to_test)} need testing. Running {len(targets)}...")
    ok_cnt, fail_cnt = 0, 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for f in as_completed({ex.submit(worker, t): t[0] for t in targets}):
            h, ok, ms = f.result()
            db[h]["last_test"] = datetime.now().isoformat()
            hist = db[h].get("history", [])
            if ok:
                ok_cnt += 1
                db[h]["success"] = db[h].get("success", 0) + 1
                hist.append(ms)
            else:
                fail_cnt += 1
                db[h]["fail"] = db[h].get("fail", 0) + 1
                hist.append(9999)
            if len(hist) > 30:
                hist = hist[-30:]
            db[h]["history"] = hist
    log(f"Done: {ok_cnt} OK, {fail_cnt} FAIL")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
