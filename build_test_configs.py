import os

content = '''import json
import os
import time
import subprocess
import re
import base64
from datetime import datetime
from Core import config_health
from Core.logger import log

DB_FILE = "database/database.json"
MAX_CONFIGS_PER_RUN = 200
PING_TIMEOUT = 5

def extract_server_address(config):
    try:
        config = config.strip()
        if config.startswith("vmess://"):
            try:
                decoded = base64.b64decode(config[8:]).decode('utf-8')
                data = json.loads(decoded)
                return data.get("add") or data.get("address")
            except Exception:
                pass
        if config.startswith("vless://"):
            match = re.search(r'vless://[^@]+@([^:]+):', config)
            if match:
                return match.group(1)
        if config.startswith("trojan://"):
            match = re.search(r'trojan://[^@]+@([^:]+):', config)
            if match:
                return match.group(1)
        if config.startswith("ss://"):
            match = re.search(r'ss://[^@]+@([^:]+):', config)
            if match:
                return match.group(1)
        if config.startswith("ssr://"):
            try:
                decoded = base64.b64decode(config[6:]).decode('utf-8')
                parts = decoded.split(':')
                if len(parts) >= 1:
                    return parts[0]
            except Exception:
                pass
        for protocol in ["hy2://", "hysteria://", "tuic://"]:
            if config.startswith(protocol):
                match = re.search(rf'{re.escape(protocol)}[^@]+@([^:]+):', config)
                if match:                    return match.group(1)
        for protocol in ["wg://", "wireguard://"]:
            if config.startswith(protocol):
                match = re.search(r'endpoint=([^:]+):', config)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        log(f"[TEST] Error: {e}")
        return None

def ping_server(address, timeout=PING_TIMEOUT):
    try:
        start_time = time.time()
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), address],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        if result.returncode == 0:
            match = re.search(r'time[=<](\\d+\\.?\\d*)', result.stdout)
            if match:
                latency_ms = float(match.group(1))
            return True, latency_ms, None
        else:
            return False, None, "Ping failed"
    except subprocess.TimeoutExpired:
        return False, None, "Timeout"
    except Exception as e:
        return False, None, str(e)

def test_single_config(config_hash, config_str):
    address = extract_server_address(config_str)
    if not address:
        return False, None, "No address"
    return ping_server(address)

def test_all_configs(db_path=DB_FILE, max_configs=MAX_CONFIGS_PER_RUN, sync_db=True):
    try:
        if not os.path.exists(db_path):
            log(f"Database not found: {db_path}")
            return {"error": "Database not found"}
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        log(f"Testing {min(len(db), max_configs)} configs...")
        log("=" * 60)
        success_count = 0        failed_count = 0
        total_latency = 0.0
        tested = 0
        for config_hash, info in list(db.items())[:max_configs]:
            config_str = info.get("config", "")
            if not config_str:
                continue
            tested += 1
            log(f"[{tested}/{min(len(db), max_configs)}] {config_hash[:16]}...", end=" ")
            success, latency, error = test_single_config(config_hash, config_str)
            config_health.update_config_health(
                config_hash=config_hash,
                success=success,
                latency=latency,
                error_message=error
            )
            if success:
                log(f"OK ({latency:.1f}ms)")
                success_count += 1
                if latency:
                    total_latency += latency
            else:
                log(f"FAIL ({error})")
                failed_count += 1
        avg_latency = total_latency / success_count if success_count > 0 else 0
        if sync_db:
            log("Syncing with database.json...")
            config_health.sync_to_database(db_path)
        summary = {
            "tested": tested,
            "success": success_count,
            "failed": failed_count,
            "success_rate": round(success_count / tested * 100, 2) if tested > 0 else 0,
            "avg_latency": round(avg_latency, 2),
            "timestamp": datetime.now().isoformat()
        }
        log("=" * 60)
        log(f"Success: {success_count}, Failed: {failed_count}")
        log(f"Rate: {summary['success_rate']}%, Avg: {summary['avg_latency']}ms")
        return summary
    except Exception as e:
        log(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    log("Starting config tests...")
    test_all_configs()
'''
os.makedirs("Core", exist_ok=True)
with open("Core/test_configs.py", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: Core/test_configs.py created")
