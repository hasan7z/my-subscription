import os
import json
import re
import random
import base64
from Core.logger import log

DB_FILE = "database/database.json"
OUTPUT_FILE = "output/jojo_style.txt"

GOLDEN_SNI = [
    'cloudflare.com', 'speedtest.net', 'tap.az', 'amazon.com',
    'microsoft.com', 'apple.com', 'google.com', 'linkedin.com',
    'vk-cdnvideo.com', 'mizulina.top', 'myfymain.com', 'cdnjst.org'
]

GOLDEN_PORTS = [443, 8443, 2053, 2083, 2087, 2096, 8880, 8080]

def is_golden_config(config_str):
    cfg_lower = config_str.lower()
    
    is_vless = cfg_lower.startswith('vless://')
    is_trojan = cfg_lower.startswith('trojan://')
    is_vmess_ss = cfg_lower.startswith('vmess://') or cfg_lower.startswith('ss://')
    
    if not (is_vless or is_trojan or is_vmess_ss):
        return False
    
    if (is_vless or is_trojan):
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
    log("🏆 STARTING JOJO STYLE (Smart Shuffle + Base64)")
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
        if not config_str or not is_golden_config(config_str):
            continue
        
        success = info.get("success", 0)
        fail = info.get("fail", 0)
        total_tests = success + fail
        
        if total_tests > 0:
            success_rate = success / total_tests
            if success_rate < 0.75:
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
    
    golden_configs.sort(key=lambda x: x["score"], reverse=True)
    log(f"📊 Found {len(golden_configs)} unique golden configs")
    
    POOL_SIZE = 150
    CHUNK_SIZE = 30
    
    actual_pool_size = min(len(golden_configs), POOL_SIZE)
    top_pool = golden_configs[:actual_pool_size]
    
    random.shuffle(top_pool)
    
    selected = top_pool[:CHUNK_SIZE]
    
    log(f"🔄 Smart Shuffle: Picked {len(selected)} fresh configs from top {actual_pool_size}")
    
    if selected:
        os.makedirs("output", exist_ok=True)
        
        raw_text = "\n".join([item["config"] for item in selected])
        
        base64_encoded = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(base64_encoded)
        
        log(f"✅ SUCCESS: Generated {OUTPUT_FILE} (Base64) with {len(selected)} FRESH configs")
        avg_score = sum(item['score'] for item in selected) / len(selected)
        log(f"   📊 Average score: {avg_score:.1f}")
    else:
        log("⚠️ WARNING: No configs selected")
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# No golden configs found at this time.\n")
    
    log("=" * 60)
    log("🏆 JOJO STYLE GENERATION COMPLETE")
    log("=" * 60)

if __name__ == "__main__":
    generate_jojo_style()
