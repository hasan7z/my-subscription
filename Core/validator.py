from Core.logger import log


VALID_PROTOCOLS = (
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
)


def validate_configs(configs):

    valid = []

    for c in configs:

        if not c:
            continue

        c = c.strip()

        if "<html" in c.lower():
            continue

        if any(c.startswith(p) for p in VALID_PROTOCOLS):
            valid.append(c)

    log(f"[VALIDATE] {len(valid)}/{len(configs)}")

    return valid
