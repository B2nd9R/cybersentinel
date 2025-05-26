import asyncio
import hashlib
import re
import json
import base64
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, parse_qs
import aiohttp
import validators

from config import Config
from core.logger import get_api_logger

logger = get_api_logger()

class TimeUtils:
    """مساعدات التوقيت"""
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """تنسيق المدة الزمنية"""
        if seconds < 60:
            return f"{seconds} ثانية"
        
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} دقيقة"
        
        hours = minutes // 60
        if hours < 24:
            return f"{hours} ساعة"
        
        days = hours // 24
        return f"{days} يوم"
    
    @staticmethod
    def get_time_diff(time1: datetime, time2: datetime) -> timedelta:
        """حساب الفرق بين وقتين"""
        return abs(time2 - time1)

class TextUtils:
    """مساعدات معالجة النصوص"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """تنظيف النص من الرموز غير المرغوب فيها"""
        # إزالة الرموز الخاصة
        text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
        # إزالة المسافات الزائدة
        text = ' '.join(text.split())
        return text
    
    @staticmethod
    def contains_arabic(text: str) -> bool:
        """التحقق من وجود نص عربي"""
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        return bool(arabic_pattern.search(text))
    
    @staticmethod
    def contains_urls(text: str) -> List[str]:
        """استخراج الروابط من النص"""
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        return url_pattern.findall(text)

class SecurityUtils:
    """مساعدات الأمان"""
    
    @staticmethod
    def hash_string(text: str) -> str:
        """إنشاء hash للنص"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    @staticmethod
    def is_safe_file(filename: str) -> bool:
        """التحقق من أمان اسم الملف"""
        # التحقق من امتداد الملف
        extension = filename.lower().split('.')[-1]
        return extension not in Config.DANGEROUS_FILE_TYPES
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """تنظيف اسم الملف"""
        # إزالة الأحرف غير الآمنة
        return re.sub(r'[^\w\-\.]', '_', filename)
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """إنشاء رمز عشوائي"""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choice(chars) for _ in range(length))

class NetworkUtils:
    """مساعدات الشبكة"""
    
    @staticmethod
    async def download_file(url: str, timeout: int = 30) -> Optional[bytes]:
        """تحميل ملف من الإنترنت"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.read()
                    return None
        except Exception as e:
            logger.error(f"خطأ في تحميل الملف: {e}")
            return None
    
    @staticmethod
    def parse_url(url: str) -> Dict[str, Any]:
        """تحليل الرابط"""
        parsed = urlparse(url)
        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'query': parse_qs(parsed.query),
            'fragment': parsed.fragment
        }
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """التحقق من صحة الرابط"""
        return validators.url(url)

class DataUtils:
    """مساعدات معالجة البيانات"""
    
    @staticmethod
    def load_json(file_path: str) -> Dict:
        """تحميل ملف JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في قراءة ملف JSON: {e}")
            return {}
    
    @staticmethod
    def save_json(data: Dict, file_path: str) -> bool:
        """حفظ بيانات في ملف JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ ملف JSON: {e}")
            return False
    
    @staticmethod
    def encode_base64(data: str) -> str:
        """تشفير النص بـ Base64"""
        return base64.b64encode(data.encode()).decode()
    
    @staticmethod
    def decode_base64(data: str) -> str:
        """فك تشفير النص من Base64"""
        try:
            return base64.b64decode(data.encode()).decode()
        except:
            return ''

class RateLimiter:
    """التحكم في معدل الطلبات"""
    
    def __init__(self, rate: int, per: float = 1.0):
        self.rate = rate  # عدد الطلبات المسموح
        self.per = per    # الفترة الزمنية بالثواني
        self.allowance = rate  # العدد المتبقي
        self.last_check = time.time()
    
    def is_allowed(self) -> bool:
        """التحقق من إمكانية تنفيذ طلب جديد"""
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        
        # تحديث العدد المتبقي
        self.allowance += time_passed * (self.rate / self.per)
        if self.allowance > self.rate:
            self.allowance = self.rate
        
        if self.allowance < 1.0:
            return False
        
        self.allowance -= 1.0
        return True
    
    async def acquire(self):
        """انتظار حتى يمكن تنفيذ الطلب"""
        while not self.is_allowed():
            await asyncio.sleep(self.per / self.rate)