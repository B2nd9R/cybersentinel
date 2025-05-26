"""
Link Guardian System
نظام حارس الروابط - فحص الروابط المشبوهة والخبيثة
"""

import asyncio
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import aiohttp
import validators

from config import Config
from core.logger import get_security_logger
from core.database import db_manager
from api.virustotal import VirusTotalAPI

logger = get_security_logger()

class LinkGuardian:
    """نظام حماية الروابط المتقدم"""
    
    def __init__(self, api_key=None):
        self.vt_api = VirusTotalAPI(api_key) if api_key else VirusTotalAPI()
        self.url_cache = {}  # كاش للروابط المفحوصة
        self.whitelist = set()  # قائمة الروابط الآمنة
        self.blacklist = set()  # قائمة الروابط الخطيرة
        
        # أنماط الروابط المشبوهة
        self.suspicious_patterns = [
            r'bit\.ly',
            r'tinyurl\.com',
            r'discord\.gift',
            r'discordapp\.gift',
            r'free.*nitro',
            r'steam.*community.*gift',
            r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+',  # IP addresses
            r'[a-z0-9]{8,}\.tk|ml|ga|cf',  # Suspicious TLDs
        ]
        
        # مجالات آمنة معروفة
        self.safe_domains = {
            'discord.com', 'discordapp.com', 'discord.gg',
            'github.com', 'youtube.com', 'youtu.be',
            'google.com', 'stackoverflow.com',
            'wikipedia.org', 'reddit.com'
        }
    
    async def scan_url(self, url: str, guild_id: int) -> Dict:
        """فحص رابط شامل"""
        try:
            # تنظيف الرابط
            cleaned_url = self._clean_url(url)
            url_hash = self._hash_url(cleaned_url)
            
            # التحقق من الكاش أولاً
            cached_result = await self._check_cache(url_hash)
            if cached_result:
                logger.info(f"🔍 استخدام نتيجة محفوظة للرابط: {cleaned_url[:50]}...")
                return cached_result
            
            # بدء الفحص
            scan_result = {
                'url': cleaned_url,
                'is_safe': True,
                'threat_level': 'safe',
                'threats': [],
                'scan_engines': [],
                'confidence': 0.0,
                'details': {}
            }
            
            # 1. فحص أساسي للرابط
            basic_check = await self._basic_url_check(cleaned_url)
            scan_result.update(basic_check)
            
            # 2. فحص الأنماط المشبوهة
            pattern_check = self._check_suspicious_patterns(cleaned_url)
            if pattern_check['is_suspicious']:
                scan_result['is_safe'] = False
                scan_result['threat_level'] = 'medium'
                scan_result['threats'].extend(pattern_check['threats'])
            
            # 3. فحص VirusTotal (إذا كان متاح)
            if Config.VIRUSTOTAL_API_KEY:
                vt_result = await self.vt_api.scan_url(cleaned_url)
                if vt_result:
                    scan_result = self._merge_vt_results(scan_result, vt_result)
            
            # 4. فحص إضافي للمحتوى
            content_check = await self._check_url_content(cleaned_url)
            if content_check:
                scan_result = self._merge_content_results(scan_result, content_check)
            
            # حفظ النتيجة في قاعدة البيانات
            await self._save_scan_result(url_hash, scan_result)
            
            logger.info(f"🔍 تم فحص الرابط: {cleaned_url[:50]}... - النتيجة: {scan_result['threat_level']}")
            return scan_result
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الرابط {url}: {e}")
            return {
                'url': url,
                'is_safe': False,
                'threat_level': 'unknown',
                'threats': ['scan_error'],
                'error': str(e)
            }
    
    def _clean_url(self, url: str) -> str:
        """تنظيف وتطبيع الرابط"""
        # إزالة المسافات والأحرف الخاصة
        url = url.strip()
        
        # إضافة http إذا لم يكن موجود
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # إزالة المعاملات المشبوهة
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        return clean_url
    
    def _hash_url(self, url: str) -> str:
        """إنشاء hash للرابط"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    async def _check_cache(self, url_hash: str) -> Optional[Dict]:
        """التحقق من الكاش"""
        # التحقق من الكاش المحلي
        if url_hash in self.url_cache:
            return self.url_cache[url_hash]
        
        # التحقق من قاعدة البيانات
        db_result = await db_manager.get_scanned_link(url_hash)
        if db_result:
            # تحويل نتيجة قاعدة البيانات إلى تنسيق مناسب
            result = {
                'url': db_result['original_url'],
                'is_safe': not db_result['is_malicious'],
                'threat_level': 'high' if db_result['is_malicious'] else 'safe',
                'virustotal_score': db_result['virustotal_score'],
                'cached': True
            }
            
            # حفظ في الكاش المحلي
            self.url_cache[url_hash] = result
            return result
        
        return None
    
    async def _basic_url_check(self, url: str) -> Dict:
        """فحص أساسي للرابط"""
        result = {
            'is_safe': True,
            'threat_level': 'safe',
            'threats': []
        }
        
        try:
            # التحقق من صحة الرابط
            if not validators.url(url):
                result['is_safe'] = False
                result['threat_level'] = 'high'
                result['threats'].append('invalid_url')
                return result
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # التحقق من القائمة السوداء
            if domain in self.blacklist:
                result['is_safe'] = False
                result['threat_level'] = 'high'
                result['threats'].append('blacklisted_domain')
            
            # التحقق من القائمة البيضاء
            elif domain in self.safe_domains:
                result['threat_level'] = 'safe'
            
            # فحص المجالات المشبوهة
            elif self._is_suspicious_domain(domain):
                result['is_safe'] = False
                result['threat_level'] = 'medium'
                result['threats'].append('suspicious_domain')
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في الفحص الأساسي: {e}")
            return {
                'is_safe': False,
                'threat_level': 'unknown',
                'threats': ['check_error']
            }
    
    def _check_suspicious_patterns(self, url: str) -> Dict:
        """فحص الأنماط المشبوهة"""
        threats = []
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                threats.append(f'suspicious_pattern_{pattern[:20]}')
        
        return {
            'is_suspicious': len(threats) > 0,
            'threats': threats
        }
    
    def _is_suspicious_domain(self, domain: str) -> bool:
        """فحص المجال للخصائص المشبوهة"""
        # مجالات قصيرة جداً
        if len(domain) < 4:
            return True
        
        # مجالات تحتوي على أرقام كثيرة
        if len(re.findall(r'\d', domain)) > len(domain) * 0.3:
            return True
        
        # مجالات عشوائية
        if len(re.findall(r'[a-z]{8,}', domain)) > 0:
            return True
        
        return False
    
    async def _check_url_content(self, url: str) -> Optional[Dict]:
        """فحص محتوى الرابط"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=False) as response:
                    # فحص رموز الاستجابة المشبوهة
                    if response.status in [301, 302, 307, 308]:
                        return {
                            'threats': ['suspicious_redirect'],
                            'details': {'redirect_status': response.status}
                        }
                    
                    # فحص headers مشبوهة
                    content_type = response.headers.get('content-type', '')
                    if 'application/octet-stream' in content_type:
                        return {
                            'threats': ['suspicious_content_type'],
                            'details': {'content_type': content_type}
                        }
        
        except asyncio.TimeoutError:
            return {
                'threats': ['connection_timeout'],
                'details': {'timeout': True}
            }
        except Exception as e:
            logger.debug(f"لا يمكن فحص محتوى الرابط: {e}")
        
        return None
    
    def _merge_vt_results(self, scan_result: Dict, vt_result: Dict) -> Dict:
        """دمج نتائج VirusTotal"""
        if vt_result.get('malicious_count', 0) > 0:
            scan_result['is_safe'] = False
            scan_result['threat_level'] = 'high'
            scan_result['threats'].extend(vt_result.get('threat_names', []))
        
        scan_result['details']['virustotal'] = vt_result
        scan_result['scan_engines'].extend(vt_result.get('engines', []))
        scan_result['confidence'] = max(scan_result['confidence'], vt_result.get('confidence', 0))
        
        return scan_result
    
    def _merge_content_results(self, scan_result: Dict, content_result: Dict) -> Dict:
        """دمج نتائج فحص المحتوى"""
        if content_result.get('threats'):
            scan_result['threats'].extend(content_result['threats'])
            if scan_result['threat_level'] == 'safe':
                scan_result['threat_level'] = 'medium'
                scan_result['is_safe'] = False
        
        scan_result['details']['content_check'] = content_result.get('details', {})
        return scan_result
    
    async def _save_scan_result(self, url_hash: str, scan_result: Dict):
        """حفظ نتيجة الفحص"""
        try:
            await db_manager.add_scanned_link(
                url_hash=url_hash,
                original_url=scan_result['url'],
                is_malicious=not scan_result['is_safe'],
                vt_score=scan_result.get('details', {}).get('virustotal', {}).get('malicious_count', 0),
                scan_engines=','.join(scan_result.get('scan_engines', [])),
                threat_names=','.join(scan_result.get('threats', []))
            )
            
            # حفظ في الكاش المحلي
            self.url_cache[url_hash] = scan_result
            
        except Exception as e:
            logger.error(f"خطأ في حفظ نتيجة الفحص: {e}")
    
    def add_to_whitelist(self, domain: str):
        """إضافة مجال للقائمة البيضاء"""
        self.whitelist.add(domain.lower())
        logger.info(f"✅ تم إضافة {domain} للقائمة البيضاء")
    
    def add_to_blacklist(self, domain: str):
        """إضافة مجال للقائمة السوداء"""
        self.blacklist.add(domain.lower())
        logger.info(f"❌ تم إضافة {domain} للقائمة السوداء")
    
    def get_stats(self) -> Dict:
        """إحصائيات النظام"""
        return {
            'cached_urls': len(self.url_cache),
            'whitelisted_domains': len(self.whitelist),
            'blacklisted_domains': len(self.blacklist)
        }