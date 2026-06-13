import re
from Core.logger import log

# پورت‌های امن TLS که در ایران کمتر فیلتر می‌شوند
SAFE_PORTS = [443, 8443, 2053, 2083, 2087, 2096, 2097]

# SNIهای معتبر که در ایران کار می‌کنند
VALID_SNIS = [
    'cloudflare.com', 'cdn.cloudflare.net', 'workers.dev',
    'google.com', 'gstatic.com', 'microsoft.com', 'apple.com',
    'amazon.com', 'aws.amazon.com', 'azure.com'
]

def is_iran_optimized(config):
    """بررسی اینکه آیا کانفیگ برای ایران بهینه شده است"""
    config_lower = config.lower()
    
    # 1. بررسی پروتکل Reality (بهترین برای ایران)
    if 'security=reality' in config_lower:
        return True, "Reality protocol"
    
    # 2. بررسی پورت‌های امن TLS
    port_match = re.search(r':(\d+)[?/]', config)
    if port_match:
        port = int(port_match.group(1))
        if port in SAFE_PORTS:
            return True, f"Safe port {port}"
    
    # 3. بررسی SNI معتبر
    sni_match = re.search(r'sni=([^&]+)', config_lower)
    if sni_match:
        sni = sni_match.group(1)
        if any(valid_sni in sni for valid_sni in VALID_SNIS):
            return True, f"Valid SNI: {sni}"
    
    # 4. بررسی WebSocket با TLS
    if 'type=ws' in config_lower and ('security=tls' in config_lower or 'tls=true' in config_lower):
        return True, "WS+TLS"
    
    return False, "Not optimized"

def filter_iran_optimized(configs):
    """فیلتر کانفیگ‌های بهینه برای ایران"""
    optimized = []
    reasons = {}
    
    for cfg in configs:
        is_opt, reason = is_iran_optimized(cfg)
        if is_opt:
            optimized.append(cfg)
            reasons[reason] = reasons.get(reason, 0) + 1
    
    log(f"🇮🇷 Iran-Optimized Filter: {len(optimized)} configs passed")
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
        log(f"   - {reason}: {count}")
    
    return optimized

if __name__ == "__main__":
    # تست
    test_configs = [
        "vless://uuid@server:443?security=reality&sni=google.com",
        "vmess://...",
        "trojan://pass@server:8443?security=tls&sni=cloudflare.com"
    ]
    result = filter_iran_optimized(test_configs)
    print(f"Optimized: {len(result)}")
