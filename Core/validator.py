import re
from core.logger import log


VALID_PROTOCOLS = [
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "ssr://",
    "hy2://",
    "hysteria://",
    "tuic://",
    "wg://",
    "wireguard://",
    "socks://",
    "http://",
    "https://"
]


def is_valid(config):
    if not config:
        return False

    config = config.strip()

    # حذف HTML یا junk
    if "<html" in config.lower():
        return False

    # بررسی پروتکل
    return any(config.startswith(p) for p in VALID_PROTOCOLS)


def validate_configs(configs):
    valid = []

    for c in configs:
        if is_valid(c):
            valid.append(c)

    log(f"[VALIDATE] valid={len(valid)} from {len(configs)}")

    return valid
