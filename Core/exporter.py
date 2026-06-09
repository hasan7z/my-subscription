import os
from core.logger import log


def detect_protocol(config):
    c = config.lower()

    if c.startswith("vmess://"):
        return "vmess"
    if c.startswith("vless://"):
        return "vless"
    if c.startswith("trojan://"):
        return "trojan"
    if c.startswith("ss://"):
        return "ss"
    if c.startswith("ssr://"):
        return "ssr"
    if c.startswith("hy2://") or "hysteria" in c:
        return "hy2"
    if c.startswith("hysteria://"):
        return "hysteria"
    if c.startswith("tuic://"):
        return "tuic"
    if c.startswith("wg://") or "wireguard" in c:
        return "wireguard"
    if c.startswith("socks://"):
        return "socks"
    if c.startswith("http://") or c.startswith("https://"):
        return "http"

    return "others"


def export_all(configs, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    buckets = {
        "all": [],
        "vmess": [],
        "vless": [],
        "trojan": [],
        "ss": [],
        "ssr": [],
        "hy2": [],
        "hysteria": [],
        "tuic": [],
        "wireguard": [],
        "socks": [],
        "http": [],
        "others": []
    }

    for c in configs:
        proto = detect_protocol(c)
        buckets["all"].append(c)
        buckets[proto].append(c)

    # نوشتن فایل‌ها
    for name, items in buckets.items():
        path = os.path.join(output_dir, f"{name}.txt")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(items))

        log(f"[EXPORT] {name}.txt -> {len(items)}")

    log("[EXPORT DONE]")
