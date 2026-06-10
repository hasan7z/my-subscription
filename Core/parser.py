import base64
import json
import re
from Core.logger import log


def parse_sources(raw_sources):

    all_configs = []

    for url, content in raw_sources.items():

        if not content:
            continue

        configs = []

        content_str = content.strip()

        # JSON
        if content_str.startswith("{") or content_str.startswith("["):
            try:
                data = json.loads(content_str)

                if isinstance(data, list):
                    configs.extend([x for x in data if isinstance(x, str)])

                elif isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, str):
                            configs.append(v)

                log(f"[PARSE] JSON {url}")

            except:
                pass

        # Base64
        elif len(content_str) > 100 and "<html" not in content_str.lower():
            try:
                decoded = base64.b64decode(content_str).decode("utf-8", errors="ignore")
                configs.extend(decoded.splitlines())
                log(f"[PARSE] BASE64 {url}")

            except:
                pass

        # Text
        else:
            configs.extend(content_str.splitlines())
            log(f"[PARSE] TEXT {url}")

        all_configs.extend(configs)

    cleaned = [
        c.strip()
        for c in all_configs
        if c and len(c.strip()) > 5
    ]

    log(f"[PARSE DONE] {len(cleaned)}")

    return cleaned
