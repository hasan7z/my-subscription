"""
تست‌کننده واقعی کانفیگ‌ها
این ماژول کانفیگ‌ها رو تست می‌کنه و نتایج رو در config_health و database ثبت می‌کنه
"""

import json
import os
import time
import subprocess
import re
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from Core import config_health
from Core.logger import log


# مسیر فایل دیتابیس
DB_FILE = "database/database.json"

# حداکثر تعداد کانفیگ برای تست در هر اجرا (برای جلوگیری از timeout)
MAX_CONFIGS_PER_RUN = 200

# Timeout برای هر تست (ثانیه)
PING_TIMEOUT = 5


def extract_server_address(config: str) -> Optional[str]:
    """
    استخراج آدرس سرور از رشته کانفیگ
    
    پشتیبانی از پروتکل‌های:
    - vmess://
    - vless://
    - trojan://
    - ss://
    - ssr://
    - hy2://
    - hysteria://
    - tuic://
    - wg://
    - wireguard://
    
    Args:
        config: رشته کانفیگ
        
    Returns:
        Optional[str]: آدرس سرور یا None اگر پیدا نشد
    """
    try:        config = config.strip()
        
        # vmess:// - فرمت Base64
        if config.startswith("vmess://"):
            import base64
            try:
                # حذف vmess:// و decode
                json_str = config[8:]
                decoded = base64.b64decode(json_str).decode('utf-8')
                data = json.loads(decoded)
                return data.get("add") or data.get("address")
            except:
                pass
        
        # vless:// - فرمت: vless://uuid@address:port?...
        if config.startswith("vless://"):
            match = re.search(r'vless://[^@]+@([^:]+):', config)
            if match:
                return match.group(1)
        
        # trojan:// - فرمت: trojan://password@address:port?...
        if config.startswith("trojan://"):
            match = re.search(r'trojan://[^@]+@([^:]+):', config)
            if match:
                return match.group(1)
        
        # ss:// - فرمت: ss://method:password@address:port
        if config.startswith("ss://"):
            match = re.search(r'ss://[^@]+@([^:]+):', config)
            if match:
                return match.group(1)
        
        # ssr:// - فرمت Base64
        if config.startswith("ssr://"):
            import base64
            try:
                decoded = base64.b64decode(config[6:]).decode('utf-8')
                # فرمت: address:port:protocol:method:obfs:password_base64/?params
                parts = decoded.split(':')
                if len(parts) >= 1:
                    return parts[0]
            except:
                pass
        
        # hy2://, hysteria://, tuic:// - فرمت مشابه
        for protocol in ["hy2://", "hysteria://", "tuic://"]:
            if config.startswith(protocol):
                match = re.search(rf'{re.escape(protocol)}[^@]+@([^:]+):', config)
                if match:
                    return match.group(1)        
        # wg://, wireguard://
        for protocol in ["wg://", "wireguard://"]:
            if config.startswith(protocol):
                # معمولاً در query string هست
                match = re.search(r'endpoint=([^:]+):', config)
                if match:
                    return match.group(1)
        
        return None
        
    except Exception as e:
        log(f"[TEST] خطا در استخراج آدرس: {e}")
        return None


def ping_server(address: str, timeout: int = PING_TIMEOUT) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    تست ping یک سرور
    
    Args:
        address: آدرس سرور
        timeout: زمان انتظار (ثانیه)
        
    Returns:
        Tuple: (success, latency_ms, error_message)
    """
    try:
        start_time = time.time()
        
        # استفاده از ping (Linux/Mac)
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), address],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        if result.returncode == 0:
            # استخراج زمان ping از output
            match = re.search(r'time[=<](\d+\.?\d*)', result.stdout)
            if match:
                latency_ms = float(match.group(1))
            
            return True, latency_ms, None
        else:
            return False, None, f"Ping failed: {result.stderr.strip()}"            
    except subprocess.TimeoutExpired:
        return False, None, "Timeout"
    except Exception as e:
        return False, None, str(e)


def test_single_config(config_hash: str, config_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    تست یک کانفیگ خاص
    
    Args:
        config_hash: هش SHA256 کانفیگ
        config_str: رشته کانفیگ
        
    Returns:
        Tuple: (success, latency_ms, error_message)
    """
    # استخراج آدرس سرور
    address = extract_server_address(config_str)
    
    if not address:
        return False, None, "آدرس سرور پیدا نشد"
    
    # تست ping
    return ping_server(address)


def test_all_configs(
    db_path: str = DB_FILE,
    max_configs: int = MAX_CONFIGS_PER_RUN,
    sync_db: bool = True
) -> Dict[str, Any]:
    """
    تست تمام کانفیگ‌ها و به‌روزرسانی اطلاعات سلامت
    
    Args:
        db_path: مسیر فایل database.json
        max_configs: حداکثر تعداد کانفیگ برای تست
        sync_db: آیا بعد از تست، database.json رو آپدیت کنه؟
        
    Returns:
        Dict: خلاصه نتایج
    """
    try:
        # بارگذاری database.json
        if not os.path.exists(db_path):
            log(f"❌ فایل دیتابیس پیدا نشد: {db_path}")
            return {"error": "Database not found"}
                with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        log(f"🧪 شروع تست {min(len(db), max_configs)} کانفیگ...")
        log("=" * 60)
        
        success_count = 0
        failed_count = 0
        total_latency = 0.0
        
        # تست کانفیگ‌ها
        tested = 0
        for config_hash, info in list(db.items())[:max_configs]:
            config_str = info.get("config", "")
            
            if not config_str:
                continue
            
            tested += 1
            log(f"[{tested}/{min(len(db), max_configs)}] تست {config_hash[:16]}...", end=" ", flush=True)
            
            # تست کانفیگ
            success, latency, error = test_single_config(config_hash, config_str)
            
            # ثبت نتیجه در config_health
            config_health.update_config_health(
                config_hash=config_hash,
                success=success,
                latency=latency,
                error_message=error
            )
            
            if success:
                log(f"✓ موفق ({latency:.1f}ms)")
                success_count += 1
                if latency:
                    total_latency += latency
            else:
                log(f"✗ ناموفق ({error})")
                failed_count += 1
        
        # محاسبه میانگین latency
        avg_latency = total_latency / success_count if success_count > 0 else 0
        
        # همگام‌سازی با database.json
        if sync_db:
            log("\n📊 همگام‌سازی با database.json...")
            config_health.sync_to_database(db_path)
        
        # خلاصه نتایج        summary = {
            "tested": tested,
            "success": success_count,
            "failed": failed_count,
            "success_rate": round(success_count / tested * 100, 2) if tested > 0 else 0,
            "avg_latency": round(avg_latency, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        log("=" * 60)
        log(f"📊 خلاصه نتایج:")
        log(f"   ✅ موفق: {success_count}")
        log(f"   ❌ ناموفق: {failed_count}")
        log(f"   📈 نرخ موفقیت: {summary['success_rate']}%")
        log(f"   ⚡ میانگین latency: {summary['avg_latency']}ms")
        
        return summary
        
    except Exception as e:
        log(f"❌ خطا در تست کانفیگ‌ها: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="تست‌کننده کانفیگ‌ها")
    parser.add_argument("--max", type=int, default=MAX_CONFIGS_PER_RUN, help="حداکثر تعداد کانفیگ")
    parser.add_argument("--no-sync", action="store_true", help="بدون همگام‌سازی با database.json")
    
    args = parser.parse_args()
    
    log("🚀 شروع تست کانفیگ‌ها")
    log(f"   حداکثر: {args.max}")
    log(f"   همگام‌سازی: {not args.no_sync}")
    log()
    
    test_all_configs(
        max_configs=args.max,
        sync_db=not args.no_sync
                  )
