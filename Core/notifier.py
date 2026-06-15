import os
import requests
from datetime import datetime
from Core.logger import log

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "hasan7z/my-subscription")
GITHUB_USERNAME = GITHUB_REPO.split("/")[0]
REPORT_FILE = "reports/status_report.md"

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log(f"⚠️ Telegram credentials not set. Skipping notification.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            log("📤 Status message sent to Telegram")
            return True
        else:
            log(f"❌ Telegram API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log(f"❌ Failed to send Telegram message: {e}")
        return False

def send_telegram_document(file_path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    if not os.path.exists(file_path):
        log(f"⚠️ File not found: {file_path}")
        return False
    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024:
        log(f"⚠️ File too large: {file_path}")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, files=files, data=data, timeout=60)
        if response.status_code == 200:
            log(f"📤 File sent: {os.path.basename(file_path)}")
            return True
        else:
            log(f"❌ Failed to send file {file_path}: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Error sending file {file_path}: {e}")
        return False

def build_pages_link(filename):
    return f"https://{GITHUB_USERNAME}.github.io/my-subscription/output/{filename}"

def check_health(db, sources_count, new_configs_count):
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    total = len(db)
    tested_configs = [i for i in db.values() if (i.get("success", 0) + i.get("fail", 0)) > 0]
    if len(tested_configs) > 0:
        active = sum(1 for i in tested_configs if i.get("success", 0) > i.get("fail", 0))
        rate = (active / len(tested_configs) * 100)
        health_str = f"{rate:.1f}%"
    else:
        health_str = "⏳ Pending Test"
    important_files = [
        ("rotation_500.txt", "🔄 Rotation 500"),
        ("iran_1.txt", "🇮🇷 Iran Mix 1"),
        ("vless_1.txt", "🔹 VLESS 1"),
        ("trojan_1.txt", "🔻 Trojan 1"),
        ("reality_1.txt", "🛡️ Reality 1"),
        ("jojo_style.txt", "🏆 JoJo Style (30 Golden)"),
        ("warp.txt", "🌀 Warp Emergency"),
        ("best_GR.txt", "🇩🇪 Germany"),
        ("subscription_base64.txt", "🔐 Base64")
    ]
    try:
        health_value = float(health_str.replace('%', ''))
        status_emoji = "✅" if health_value > 50 else "⚠️"
    except:
        status_emoji = "⏳"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    msg = f"{status_emoji} *Smart Subscription Updated*\n"
    msg += f"🕐 _{now_str}_\n\n"
    msg += f"📊 *Live Stats:*\n"
    msg += f"├ 🗄️ Total DB: `{total}`\n"
    msg += f"├ ❤️ Health Rate: `{health_str}`\n"
    msg += f"├ 🔗 Active Sources: `{sources_count}`\n"
    msg += f"└ 🆕 New Configs: `{new_configs_count}`\n\n"
    msg += f"📥 *Quick Access Links:*\n"
    file_info_for_docs = []
    for fname, label in important_files:
        fpath = f"output/{fname}"
        link = build_pages_link(fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                count = len([l for l in f if l.strip()])
            msg += f"▫️ *{label}* (`{count}`)\n"
            msg += f"   └ [Open Link]({link})\n"
            file_info_for_docs.append((fpath, label, count))
        else:
            msg += f"▫️ *{label}* (Not generated)\n"
    msg += f"\n🔗 *Full Dashboard:*\n👉 [Click Here](https://github.com/{GITHUB_REPO})"
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(msg.replace("*", "").replace("_", ""))
    log(f"📋 Report saved to {REPORT_FILE}")
    send_telegram_message(msg)
    log("📎 Sending files as documents...")
    sent_count = 0
    for fpath, label, count in file_info_for_docs:
        caption = f"{label}\nCount: {count}\n🕐 {now_str}"
        if send_telegram_document(fpath, caption):
            sent_count += 1
    log(f"✅ Notification complete: {sent_count} files sent.")
    return True

if __name__ == "__main__":
    test_db = {"h1": {"success": 10, "fail": 2}, "h2": {"success": 0, "fail": 0}}
    check_health(test_db, 15, 500)
