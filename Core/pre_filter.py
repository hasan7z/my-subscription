VALID_PREFIX = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "ssr://",
    "hy2://",
    "hysteria://",
    "tuic://"
)


def fast_filter(lines):

    result = []

    for line in lines:

        line = line.strip()

        if line.startswith(VALID_PREFIX):
            result.append(line)

    return result
