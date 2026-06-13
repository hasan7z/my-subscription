import re
from Core.logger import log

SOURCES_FILE = "Sources/sources.txt"

def extract_urls_from_content(content):
    """استخراج لینک‌های معتبر از محتوای دانلود شده"""
    if not content:
        return []
    
    # الگوی شناسایی لینک‌های HTTP/HTTPS
    url_pattern = r'https?://[^\s<>"\']+'
    urls = re.findall(url_pattern, content)
    
    # فیلتر لینک‌های معتبر
    valid_urls = []
    for url in urls:
        url = url.strip().rstrip('/')
        # حذف لینک‌های بی‌کیفیت
        if any(bad in url.lower() for bad in ['telegram.me', 't.me/', 'youtube', 'twitter']):
            continue
        # فقط لینک‌هایی که احتمالاً ساب هستند
        if any(good in url.lower() for good in ['raw.githubusercontent', 'jsdelivr', '.txt', '.json', '/sub/', 'github.com']):
            valid_urls.append(url)
    
    return list(set(valid_urls))

def process(raw_content):
    """پردازش محتوای خام و اضافه کردن لینک‌های جدید به sources.txt"""
    import os
    
    if not os.path.exists(SOURCES_FILE):
        os.makedirs(os.path.dirname(SOURCES_FILE), exist_ok=True)
        with open(SOURCES_FILE, 'w', encoding='utf-8') as f:
            f.write('')
    
    # خواندن لینک‌های فعلی
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        existing_urls = set(line.strip() for line in f if line.strip())
    
    # استخراج لینک‌های جدید از همه محتوا
    new_urls = set()
    for url, content in raw_content.items():
        extracted = extract_urls_from_content(content)
        new_urls.update(extracted)
    
    # حذف لینک‌های تکراری
    urls_to_add = new_urls - existing_urls
    
    # اضافه کردن به فایل
    if urls_to_add:
        with open(SOURCES_FILE, 'a', encoding='utf-8') as f:
            for url in urls_to_add:
                f.write(url + '\n')
        log(f"[AUTO SOURCE] Added {len(urls_to_add)} new sources")
    else:
        log("[AUTO SOURCE] No new sources found")
    
    return len(urls_to_add)
