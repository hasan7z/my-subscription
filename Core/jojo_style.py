import os
import re
import random
from Core.logger import log

SOURCE_FILE = "output/best_iran.txt"
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
        port = int(port_match.group(1))
        if port not in GOLDEN_PORTS:
            return False
    
    sni_match = re.search(r'sni=([^&]+)', cfg_lower)
    if sni_match:
        sni = sni_match.group(1)
        if not any(golden_sni in sni for golden_sni in GOLDEN_SNI):
            return False
    
    if 'allowinsecure=1' in cfg_lower or 'allowinsecure=true' in cfg_lower:
        return False
    
    return True

def extract_server_ip(config_str):
    match = re.search(r'@([^:]+):', config_str)
    if match:
        return match.group(1)
    return None
def generate_jojo_style():
    log("=" * 60)
    log("🏆 STARTING JOJO STYLE GENERATION (Lightweight Mode)")
    log("=" * 60)
    
    if not os.path.exists(SOURCE_FILE):
        log(f"❌ ERROR: {SOURCE_FILE} not found! Cannot generate JoJo style.")
        return
    
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        configs = [line.strip() for line in f if line.strip()]
        
    log(f"✅ Loaded {len(configs)} configs from {SOURCE_FILE}")
    
    golden_configs = []
    seen_servers = set()
    
    for config_str in configs:
        if not is_golden_config(config_str):
            continue
        
        server_ip = extract_server_ip(config_str)
        if server_ip and server_ip in seen_servers:
            continue
        
        score = random.uniform(70, 100)
        
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
            
    log(f"📊 Found {len(golden_configs)} unique golden configs matching criteria")
    
    golden_configs.sort(key=lambda x: x["score"], reverse=True)
    top_30 = golden_configs[:30]
    
    if top_30:
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for item in top_30:
                f.write(item["config"] + "\n")
        
        log(f"✅ SUCCESS: Generated {OUTPUT_FILE} with {len(top_30)} configs")
        unique_in_output = len(set(item['server'] for item in top_30 if item['server']))
        log(f"   📊 Unique servers in output: {unique_in_output}")
    else:
        log("⚠️ WARNING: No golden configs found matching criteria.")
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# No golden configs found at this time.\n")
            
    log("=" * 60)
    log("🏆 JOJO STYLE GENERATION COMPLETE")
    log("=" * 60)

if __name__ == "__main__":
    generate_jojo_style()
