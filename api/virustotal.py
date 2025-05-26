"""
VirusTotal API Integration
تكامل مع خدمة VirusTotal لفحص الروابط والملفات
"""

import asyncio
import aiohttp
import hashlib
import base64
from typing import Dict, Optional, List
from urllib.parse import urlparse

from config import Config
from core.logger import get_security_logger

logger = get_security_logger()

class VirusTotalAPI:
    """واجهة برمجة تطبيقات VirusTotal"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.VIRUSTOTAL_API_KEY
        self.base_url = "https://www.virustotal.com/vtapi/v2"
        self.session = None
        
        # حدود الطلبات
        self.rate_limit = {
            'requests_per_minute': 4,
            'last_request_time': 0,
            'request_count': 0
        }
    
    async def initialize(self):
        """تهيئة الجلسة"""
        if not self.api_key:
            logger.warning("⚠️ لم يتم توفير مفتاح VirusTotal API")
            return False
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'CyberSentinel-Bot/1.0'}
        )
        
        # اختبار الاتصال
        test_result = await self._test_connection()
        if test_result:
            logger.info("✅ تم الاتصال بـ VirusTotal بنجاح")
            return True
        else:
            logger.error("❌ فشل الاتصال بـ VirusTotal")
            return False
    
    async def close(self):
        """إغلاق الجلسة"""
        if self.session:
            await self.session.close()
    
    async def scan_url(self, url: str) -> Optional[Dict]:
        """فحص رابط باستخدام VirusTotal"""
        if not self.session or not self.api_key:
            return None
        
        try:
            # التحقق من حدود الطلبات
            if not await self._check_rate_limit():
                logger.warning("تم تجاوز حد الطلبات لـ VirusTotal")
                return None
            
            # إرسال الرابط للفحص
            scan_id = await self._submit_url(url)
            if not scan_id:
                return None
            
            # انتظار قصير ثم الحصول على النتيجة
            await asyncio.sleep(2)
            result = await self._get_scan_report(scan_id)
            
            return self._parse_scan_result(result, url)
            
        except Exception as e:
            logger.error(f"خطأ في فحص الرابط {url}: {e}")
            return None
    
    async def scan_file_hash(self, file_hash: str) -> Optional[Dict]:
        """فحص ملف باستخدام الهاش"""
        if not self.session or not self.api_key:
            return None
        
        try:
            if not await self._check_rate_limit():
                return None
            
            params = {
                'apikey': self.api_key,
                'resource': file_hash
            }
            
            async with self.session.get(
                f"{self.base_url}/file/report",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_file_result(data)
                else:
                    logger.error(f"خطأ في فحص الملف: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"خطأ في فحص الملف {file_hash}: {e}")
            return None
    
    async def get_domain_report(self, domain: str) -> Optional[Dict]:
        """الحصول على تقرير النطاق"""
        if not self.session or not self.api_key:
            return None
        
        try:
            if not await self._check_rate_limit():
                return None
            
            params = {
                'apikey': self.api_key,
                'domain': domain
            }
            
            async with self.session.get(
                f"{self.base_url}/domain/report",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_domain_result(data)
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"خطأ في فحص النطاق {domain}: {e}")
            return None
    
    async def _submit_url(self, url: str) -> Optional[str]:
        """إرسال رابط للفحص"""
        try:
            data = {
                'apikey': self.api_key,
                'url': url
            }
            
            async with self.session.post(
                f"{self.base_url}/url/scan",
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('scan_id')
                else:
                    logger.error(f"فشل إرسال الرابط للفحص: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"خطأ في إرسال الرابط: {e}")
            return None
    
    async def _get_scan_report(self, scan_id: str) -> Optional[Dict]:
        """الحصول على تقرير الفحص"""
        try:
            params = {
                'apikey': self.api_key,
                'resource': scan_id
            }
            
            async with self.session.get(
                f"{self.base_url}/url/report",
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"خطأ في الحصول على التقرير: {e}")
            return None
    
    def _parse_scan_result(self, result: Dict, url: str) -> Dict:
        """تحليل نتيجة فحص الرابط"""
        if not result:
            return {
                'url': url,
                'is_malicious': False,
                'scan_engines': 0,
                'positive_detections': 0,
                'scan_date': None,
                'threat_names': []
            }
        
        scans = result.get('scans', {})
        positive_count = sum(1 for scan in scans.values() if scan.get('detected', False))
        total_scans = len(scans)
        
        threat_names = [
            scan.get('result', '') for scan in scans.values() 
            if scan.get('detected', False) and scan.get('result')
        ]
        
        return {
            'url': url,
            'is_malicious': positive_count > 0,
            'scan_engines': total_scans,
            'positive_detections': positive_count,
            'scan_date': result.get('scan_date'),
            'threat_names': threat_names,
            'permalink': result.get('permalink'),
            'response_code': result.get('response_code')
        }
    
    def _parse_file_result(self, result: Dict) -> Dict:
        """تحليل نتيجة فحص الملف"""
        if not result:
            return {'is_malicious': False, 'scan_engines': 0}
        
        scans = result.get('scans', {})
        positive_count = sum(1 for scan in scans.values() if scan.get('detected', False))
        
        return {
            'is_malicious': positive_count > 0,
            'scan_engines': len(scans),
            'positive_detections': positive_count,
            'scan_date': result.get('scan_date'),
            'md5': result.get('md5'),
            'sha1': result.get('sha1'),
            'sha256': result.get('sha256')
        }
    
    def _parse_domain_result(self, result: Dict) -> Dict:
        """تحليل نتيجة فحص النطاق"""
        if not result:
            return {'is_malicious': False}
        
        # تحليل النتائج من محركات مختلفة
        detected_urls = result.get('detected_urls', [])
        undetected_urls = result.get('undetected_urls', [])
        
        return {
            'domain': result.get('domain'),
            'is_malicious': len(detected_urls) > 0,
            'detected_urls_count': len(detected_urls),
            'undetected_urls_count': len(undetected_urls),
            'categories': result.get('categories', []),
            'whois_timestamp': result.get('whois_timestamp')
        }
    
    async def _check_rate_limit(self) -> bool:
        """التحقق من حدود الطلبات"""
        import time
        current_time = time.time()
        
        # إعادة تعيين العداد كل دقيقة
        if current_time - self.rate_limit['last_request_time'] > 60:
            self.rate_limit['request_count'] = 0
            self.rate_limit['last_request_time'] = current_time
        
        # التحقق من الحد الأقصى
        if self.rate_limit['request_count'] >= self.rate_limit['requests_per_minute']:
            return False
        
        self.rate_limit['request_count'] += 1
        return True
    
    async def _test_connection(self) -> bool:
        """اختبار الاتصال بـ VirusTotal"""
        try:
            # فحص رابط آمن معروف للاختبار
            test_url = "https://www.google.com"
            result = await self.scan_url(test_url)
            return result is not None
            
        except Exception as e:
            logger.error(f"فشل اختبار الاتصال: {e}")
            return False
    
    @staticmethod
    def calculate_file_hash(file_content: bytes, hash_type: str = 'sha256') -> str:
        """حساب هاش الملف"""
        if hash_type == 'md5':
            return hashlib.md5(file_content).hexdigest()
        elif hash_type == 'sha1':
            return hashlib.sha1(file_content).hexdigest()
        elif hash_type == 'sha256':
            return hashlib.sha256(file_content).hexdigest()
        else:
            raise ValueError(f"نوع هاش غير مدعوم: {hash_type}")