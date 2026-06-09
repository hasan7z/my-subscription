import base64
import json
import re
from core.logger import log


def parse_sources(raw_sources):
    """
    ورودی: dict {url: content}
    خروجی: list of raw configs
    """

    all_configs = []

    for url, content in raw_sources.items():

        if not content:
            continue

        configs = []

        # JSON source
        if content.strip().startswith("{") or content.strip().startswith("["):
            try:
                data = json.loads(content)

                # اگر لیست URL بود
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            configs.append(item)

                # اگر dict بود
                elif isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, str):
                            configs.append(v)

                log(f"[PARSE] JSON -> {url}")

            except Exception:
                pass

        # Base64 detection
        elif len(content) > 100 and not "<html" in content.lower():
            try:
                decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                configs.extend(decoded.splitlines())
                log(f"[PARSE] BASE64 -> {url}")

            except Exception:
                pass

        # HTML filter
        elif "<html" in content.lower():
            log(f"[SKIP] HTML ignored -> {url}")
            continue

        # Plain text
        else:
            configs.extend(content.splitlines())
            log(f"[PARSE] TEXT -> {url}")

        all_configs.extend(configs)

    # پاکسازی اولیه
    cleaned = [c.strip() for c in all_configs if c and len(c.strip()) > 5]

    log(f"[PARSE DONE] total={len(cleaned)}")

    return cleaned
