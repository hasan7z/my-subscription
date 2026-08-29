import json
import base64
import urllib.parse
import socket
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 3  # ثانیه
MAX_WORKERS = 50  # تعداد تست همزمان (مناسب برای گیت‌هاب اکشنز)

def extract_addr_and_port(cfg):
    """استخراج دقیق آدرس و پورت از انواع کانفیگ"""
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
                    
        # پردازش VMess (که واقعاً Base64 است)
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
    """بررسی سلامت با اتصال TCP (سازگار با GitHub Actions)"""
    try:
        t0 = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))        sock.close()
        
        if result == 0:
            latency = round((time.time() - t0) * 1000, 2)
            return True, latency, None
        return False, None, "connection_refused"
    except socket.timeout:
        return False, None, "timeout"
    except Exception as e:
        return False, None, str(e)

def process_config(hash_key, info):
    """پردازش یک کانفیگ و به‌روزرسانی دیتابیس"""
    cfg_str = info.get("config", "")
    host, port = extract_addr_and_port(cfg_str)
    
    if not host or not port:
        return hash_key, False, None, "invalid_format"
        
    is_up, latency, error = check_tcp_health(host, port)
    return hash_key, is_up, latency, error

def main():
    db_file = "database/database.json"
    if not os.path.exists(db_file):
        print("❌ Database file not found!")
        return

    print("📂 Loading database...")
    with open(db_file, "r", encoding="utf-8") as f:
        db = json.load(f)

    print(f"🚀 Starting TCP Health Check for {len(db)} configs...")
    updated_count = 0
    
    # استفاده از ThreadPool برای سرعت بالا در گیت‌هاب اکشنز
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_config, h, info): h for h, info in db.items()}
        
        for future in as_completed(futures):
            hash_key, is_up, latency, error = future.result()
            
            if is_up:
                db[hash_key]["success"] = db[hash_key].get("success", 0) + 1
                db[hash_key]["fail"] = db[hash_key].get("fail", 0)
                db[hash_key]["last_latency"] = latency
                db[hash_key]["history"] = db[hash_key].get("history", [])[-19:] + [latency]
            else:
                db[hash_key]["success"] = db[hash_key].get("success", 0)
                db[hash_key]["fail"] = db[hash_key].get("fail", 0) + 1                db[hash_key]["history"] = db[hash_key].get("history", [])[-19:] + [9999]
            
            updated_count += 1
            if updated_count % 500 == 0:
                print(f"✅ Processed {updated_count}/{len(db)} configs...")

    print("💾 Saving updated database...")
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        
    print("🎉 Health check completed successfully!")

if __name__ == "__main__":
    main()
