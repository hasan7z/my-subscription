import json
import base64
import socket
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 5  # افزایش زمان انتظار برای اطمینان بیشتر
MAX_WORKERS = 30  # کاهش تعداد همزمان برای جلوگیری از مسدود شدن توسط گیت‌هاب

def extract_addr_and_port(cfg):
    try:
        cfg = cfg.strip()
        # پردازش VLESS و Trojan
        if cfg.startswith("vless://") or cfg.startswith("trojan://"):
            parts = cfg.split("://")[1]
            auth_and_host = parts.split("?")[0]
            if "@" in auth_and_host:
                address_port = auth_and_host.split("@")[1]
                if ":" in address_port:
                    host, port = address_port.rsplit(":", 1)
                    return host, int(port)
                    
        # پردازش VMess
        elif cfg.startswith("vmess://"):
            b64 = cfg[8:] + "=" * ((4 - len(cfg[8:]) % 4) % 4)
            data = json.loads(base64.b64decode(b64).decode("utf-8", errors="ignore"))
            return data.get("add", ""), int(data.get("port", 443))
            
        # پردازش Shadowsocks
        elif cfg.startswith("ss://"):
            if "@" in cfg:
                host_port = cfg.split("@")[1].split("?")[0]
                if ":" in host_port:
                    host, port = host_port.rsplit(":", 1)
                    return host, int(port)
                    
    except Exception:
        pass
    return None, None

def check_tcp_health(host, port, timeout=TIMEOUT):
    try:
        t0 = time.time()
        # ابتدا تست DNS
        ip = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()        
        if result == 0:
            latency = round((time.time() - t0) * 1000, 2)
            return True, latency, "OK"
        else:
            return False, -1, f"Connection Failed (Code: {result})"
    except socket.gaierror:
        return False, -1, "DNS Resolution Failed"
    except socket.timeout:
        return False, -1, "Socket Timeout"
    except Exception as e:
        return False, -1, str(e)

def main():
    db_file = "database/database.json"
    if not os.path.exists(db_file):
        print("❌ Database file not found!")
        return

    print("📂 Loading database...")
    with open(db_file, "r", encoding="utf-8") as f:
        db = json.load(f)

    print(f"🚀 Starting TCP Health Check for {len(db)} configs...")
    
    debug_logs = []
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_tcp_health, *extract_addr_and_port(info.get("config", "")), h): h for h, info in db.items()}
        
        for future in as_completed(futures):
            hash_key = futures[future]
            try:
                is_up, latency, error = future.result()
            except Exception as e:
                is_up, latency, error = False, -1, f"Crash: {str(e)}"

            if is_up:
                db[hash_key]["success"] = db[hash_key].get("success", 0) + 1
                db[hash_key]["last_latency"] = latency
                db[hash_key]["history"] = db[hash_key].get("history", [])[-19:] + [latency]
                success_count += 1
            else:
                db[hash_key]["fail"] = db[hash_key].get("fail", 0) + 1
                db[hash_key]["history"] = db[hash_key].get("history", [])[-19:] + [9999]
                fail_count += 1
                
                # ذخیره ۲۰ خطای اول برای دیباگ                if len(debug_logs) < 20:
                    host, port = extract_addr_and_port(db[hash_key].get("config", ""))
                    debug_logs.append(f"❌ FAIL: {host}:{port} -> {error}")

    print("\n" + "="*50)
    print(f"📊 RESULTS: {success_count} SUCCESS | {fail_count} FAILED")
    print("="*50)
    
    if debug_logs:
        print("🔍 DEBUG INFO (First 20 failures):")
        for log in debug_logs:
            print(log)
    else:
        print("✅ All configs passed or no failures to report!")

    print("💾 Saving updated database...")
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print("🎉 Health check completed!")

if __name__ == "__main__":
    main()
