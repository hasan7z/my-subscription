import requests
import time
from core.logger import log


DEFAULT_TIMEOUT = 20
RETRY_COUNT = 3


def fetch_url(url, retry=RETRY_COUNT, timeout=DEFAULT_TIMEOUT):
    """
    دانلود یک URL و برگرداندن متن آن
    """
    for attempt in range(1, retry + 1):
        try:
            log(f"[DOWNLOAD] Attempt {attempt} -> {url}")

            r = requests.get(url, timeout=timeout)

            if r.status_code == 200:
                return r.text

            log(f"[ERROR] Status {r.status_code} for {url}")

        except Exception as e:
            log(f"[ERROR] Exception on {url}: {str(e)}")

        time.sleep(1)

    log(f"[FAILED] Giving up: {url}")
    return None


def download_sources(sources):
    """
    دانلود همه منابع
    خروجی: dict {url: content}
    """
    results = {}

    for url in sources:
        content = fetch_url(url)

        if content:
            results[url] = content

    log(f"[DOWNLOAD DONE] success={len(results)} total={len(sources)}")

    return results
