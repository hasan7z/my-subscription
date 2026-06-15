import os
import json
import re
from Core.logger import log

DB_FILE = "database/database.json"
OUTPUT_FILE = "output/jojo_style.txt"

GOLDEN_SNI = [
    'cloudflare.com', 'speedtest.net', 'tap.az', 'amazon.com',
    'microsoft.com', 'apple.com', 'google.com', 'linkedin.com',
    'yahoo.com', 'cdn.discordapp.com', 'amd.com', 'www.speedtest.net'
]

GOLDEN_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

def is_golden_config(config_str):
    cfg_lower = config_str.lower()
    if not (cfg_lower.startswith('vless://') or cfg_lower.startswith('trojan://')):
        return False
    if 'security=tls' not in cfg_lower and 'security=reality' not in cfg_lower:
        return False
    port_match = re.search(r':(\d+)[?/]', config_str)
    if port_match:
        if int(port_match.group(1)) not in GOLDEN_PORTS:
            return False
    sni_match = re.search(r'sni=([^&]+)', cfg_lower)
    if sni_match:
        if not any(sni in sni_match.group(1) for sni in GOLDEN_SNI):
            return False
    if 'allowinsecure=1' in cfg_lower or 'allowinsecure=true' in cfg_lower:
        return False
    return True

def extract_server_ip(config_str):
    match = re.search(r'@([^:]+):', config_str)
    return match.group(1) if match else None

def generate_jojo_style():
    log("=" * 60)
    log("🏆 STARTING JOJO STYLE GENERATION")
    log("=" * 60)
    if not os.path.exists(DB_FILE):
        log(f"❌ ERROR: {DB_FILE} not found!")
        return
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    log(f"✅ Database loaded: {len(db)} total configs")
    golden_configs = []
    seen_servers = set()
    for cfg_hash, info in db.items():
        config_str = info.get("config", "")
        if not config_str:
            continue
        if not is_golden_config(config_str):
            continue
        success = info.get("success", 0)
        fail = info.get("fail", 0)
        total_tests = success + fail
        if total_tests > 0:
            success_rate = success / total_tests
            if success_rate < 0.8:
                continue
            score = success_rate * 100
        else:
            score = 70
        server_ip = extract_server_ip(config_str)
        if server_ip and server_ip in seen_servers:
            continue
        cfg_lower = config_str.lower()
        if any(kw in cfg_lower for kw in ['de', '🇩🇪', 'germany', 'frankfurt']):
            score += 10
        elif any(kw in cfg_lower for kw in ['tr', '🇹🇷', 'turkey']):
            score += 8
        golden_configs.append({
            "config": config_str,
            "score": score,
            "server": server_ip
        })
        if server_ip:
            seen_servers.add(server_ip)
    log(f"📊 Found {len(golden_configs)} unique golden configs")
    golden_configs.sort(key=lambda x: x["score"], reverse=True)
    top_30 = golden_configs[:30]
    if top_30:
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for item in top_30:
                f.write(item["config"] + "\n")
        log(f"✅ SUCCESS: Generated {OUTPUT_FILE} with {len(top_30)} configs")
        avg_score = sum(item['score'] for item in top_30) / len(top_30)
        log(f"   📊 Average score: {avg_score:.1f}")
    else:
        log("⚠️ WARNING: No golden configs found")
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# No golden configs found at this time.\n")
    log("=" * 60)
    log("🏆 JOJO STYLE GENERATION COMPLETE")
    log("=" * 60)

if __name__ == "__main__":
    generate_jojo_style()
