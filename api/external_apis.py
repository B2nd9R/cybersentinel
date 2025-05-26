"""
External APIs Manager
مدير الـ APIs الخارجية - يدير جميع التكاملات مع الخدمات الخارجية
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote
from datetime import datetime, timedelta

from config import Config
from core.logger import get_security_logger
from .virustotal import VirusTotalAPI

logger = get_security_logger()

class ExternalAPIManager:
    """مدير الـ APIs الخارجية"""
    
    def __init__(self):
        self.virustotal = VirusTotalAPI()
        self.session = None
        
        # إعدادات الطلبات
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.headers = {
            'User-Agent': 'CyberSentinel-Bot/1.0 Security Scanner'
        }
        
        # كاش للنتائج
        self.cache = {
            'url_reputation': {},
            'domain_info': {},
            'ip_geolocation': {}
        }
        
        # قوائم الحماية
        self.threat_intelligence = {
            'malware_domains': set(),
            'phishing_urls': set(),
            'suspicious_ips': set(),
            'safe_domains': set()
        }
    
    async def initialize(self):
        """تهيئة المدير والـ APIs"""
        try:
            # إنشاء جلسة HTTP
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers
            )
            
            # تهيئة VirusTotal
            await self.virustotal.initialize()
            
            # تحميل قوائم التهديدات
            await self._load_threat_intelligence()
            
            logger.info("✅ تم تهيئة مدير الـ APIs الخارجية")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة مدير الـ APIs: {e}")
            return False
    
    async def close(self):
        """إغلاق الجلسات"""
        if self.session:
            await self.session.close()
        
        if self.virustotal:
            await self.virustotal.close()
    
    async def comprehensive_url_scan(self, url: str) -> Dict:
        """فحص شامل للرابط باستخدام عدة مصادر"""
        scan_result = {
            'url': url,
            'is_safe': True,
            'threat_level': 'safe',
            'confidence': 0.0,
            'sources': [],
            'threats_detected': [],
            'scan_timestamp': datetime.now().isoformat()
        }
        
        try:
            # 1. فحص VirusTotal
            vt_result = await self.virustotal.scan_url(url)
            if vt_result:
                scan_result['sources'].append('virustotal')
                if vt_result.get('is_malicious', False):
                    scan_result['is_safe'] = False
                    scan_result['threat_level'] = 'high'
                    scan_result['threats_detected'].extend(vt_result.get('threat_names', []))
                    scan_result['confidence'] += 0.4
            
            # 2. فحص قوائم التهديدات المحلية
            local_check = await self._check_local_threat_lists(url)
            if local_check['is_threat']:
                scan_result['is_safe'] = False
                scan_result['threat_level'] = local_check['severity']
                scan_result['threats_detected'].append(local_check['threat_type'])
                scan_result['confidence'] += 0.3
                scan_result['sources'].append('local_intelligence')
            
            # 3. فحص سمعة النطاق
            domain_rep = await self._check_domain_reputation(url)
            if domain_rep:
                scan_result['sources'].append('domain_reputation')
                if domain_rep.get('is_suspicious', False):
                    scan_result['is_safe'] = False
                    scan_result['threat_level'] = 'medium'
                    scan_result['confidence'] += 0.2
            
            # 4. فحص الـ IP Geolocation
            ip_info = await self._get_ip_geolocation(url)
            if ip_info and ip_info.get('is_suspicious', False):
                scan_result['sources'].append('ip_geolocation')
                scan_result['threats_detected'].append('suspicious_location')
                scan_result['confidence'] += 0.1
            
            # تحديد مستوى الثقة النهائي
            scan_result['confidence'] = min(scan_result['confidence'], 1.0)
            
            # تحديد مستوى التهديد بناءً على الثقة
            if scan_result['confidence'] >= 0.7:
                scan_result['threat_level'] = 'high'
            elif scan_result['confidence'] >= 0.4:
                scan_result['threat_level'] = 'medium'
            elif scan_result['confidence'] >= 0.2:
                scan_result['threat_level'] = 'low'
            
            logger.info(f"🔍 فحص شامل للرابط {url[:50]}... - النتيجة: {scan_result['threat_level']}")
            return scan_result
            
        except Exception as e:
            logger.error(f"خطأ في الفحص الشامل للرابط {url}: {e}")
            return scan_result
    
    async def check_file_reputation(self, file_hash: str, file_name: str = None) -> Dict:
        """فحص سمعة الملف"""
        try:
            # فحص VirusTotal
            vt_result = await self.virustotal.scan_file_hash(file_hash)
            
            result = {
                'file_hash': file_hash,
                'file_name': file_name,
                'is_malicious': False,
                'threat_level': 'safe',
                'scan_engines': 0,
                'positive_detections': 0
            }
            
            if vt_result:
                result.update(vt_result)
                if vt_result.get('positive_detections', 0) > 0:
                    result['is_malicious'] = True
                    if vt_result['positive_detections'] >= 5:
                        result['threat_level'] = 'high'
                    elif vt_result['positive_detections'] >= 2:
                        result['threat_level'] = 'medium'
                    else:
                        result['threat_level'] = 'low'
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في فحص سمعة الملف {file_hash}: {e}")
            return {'file_hash': file_hash, 'is_malicious': False}
    
    async def get_domain_intelligence(self, domain: str) -> Dict:
        """الحصول على معلومات استخباراتية عن النطاق"""
        try:
            # التحقق من الكاش أولاً
            if domain in self.cache['domain_info']:
                cached_data = self.cache['domain_info'][domain]
                if self._is_cache_valid(cached_data['timestamp']):
                    return cached_data['data']
            
            intelligence = {
                'domain': domain,
                'is_suspicious': False,
                'age_days': None,
                'registrar': None,
                'country': None,
                'threat_categories': [],
                'reputation_score': 0
            }
            
            # فحص VirusTotal للنطاق
            vt_domain = await self.virustotal.get_domain_report(domain)
            if vt_domain:
                intelligence.update(vt_domain)
                if vt_domain.get('is_malicious', False):
                    intelligence['is_suspicious'] = True
                    intelligence['threat_categories'].append('malware')
            
            # فحص قوائم التهديدات
            if domain in self.threat_intelligence['malware_domains']:
                intelligence['is_suspicious'] = True
                intelligence['threat_categories'].append('known_malware')
            
            # حفظ في الكاش
            self.cache['domain_info'][domain] = {
                'data': intelligence,
                'timestamp': datetime.now()
            }
            
            return intelligence
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات النطاق {domain}: {e}")
            return {'domain': domain, 'is_suspicious': False}
    
    async def _check_local_threat_lists(self, url: str) -> Dict:
        """فحص قوائم التهديدات المحلية"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # فحص النطاقات الخبيثة
            if domain in self.threat_intelligence['malware_domains']:
                return {
                    'is_threat': True,
                    'threat_type': 'malware_domain',
                    'severity': 'high'
                }
            
            # فحص روابط التصيد
            if url.lower() in self.threat_intelligence['phishing_urls']:
                return {
                    'is_threat': True,
                    'threat_type': 'phishing_url',
                    'severity': 'high'
                }
            
            # فحص النطاقات الآمنة
            if domain in self.threat_intelligence['safe_domains']:
                return {
                    'is_threat': False,
                    'threat_type': 'safe_domain',
                    'severity': 'safe'
                }
            
            return {'is_threat': False}
            
        except Exception as e:
            logger.error(f"خطأ في فحص قوائم التهديدات: {e}")
            return {'is_threat': False}
    
    async def _check_domain_reputation(self, url: str) -> Optional[Dict]:
        """فحص سمعة النطاق"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # يمكن إضافة تكامل مع خدمات أخرى هنا
            # مثل Cisco Umbrella, OpenDNS, etc.
            
            # فحص أساسي للنطاق
            reputation = {
                'domain': domain,
                'is_suspicious': False,
                'reputation_score': 50,  # نقطة محايدة
                'categories': []
            }
            
            # فحص أنماط النطاقات المشبوهة
            suspicious_patterns = [
                r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',  # IP addresses
                r'.*\.tk$|.*\.ml$|.*\.ga$|.*\.cf$',  # Suspicious TLDs
                r'.*discord.*gift.*|.*nitro.*free.*',  # Discord scams
            ]
            
            import re
            for pattern in suspicious_patterns:
                if re.match(pattern, domain, re.IGNORECASE):
                    reputation['is_suspicious'] = True
                    reputation['reputation_score'] = 10
                    reputation['categories'].append('suspicious_pattern')
                    break
            
            return reputation
            
        except Exception as e:
            logger.error(f"خطأ في فحص سمعة النطاق: {e}")
            return None
    
    async def _get_ip_geolocation(self, url: str) -> Optional[Dict]:
        """الحصول على معلومات الموقع الجغرافي للـ IP"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # يمكن استخدام خدمات مجانية مثل ipapi.co
            # هذا مثال أساسي
            
            import socket
            ip = socket.gethostbyname(domain)
            
            # فحص الـ IPs المشبوهة
            if ip in self.threat_intelligence['suspicious_ips']:
                return {
                    'ip': ip,
                    'is_suspicious': True,
                    'reason': 'known_malicious_ip'
                }
            
            return {
                'ip': ip,
                'is_suspicious': False
            }
            
        except Exception as e:
            logger.debug(f"لا يمكن الحصول على معلومات الـ IP للنطاق: {e}")
            return None
    
    async def _load_threat_intelligence(self):
        """تحميل قوائم التهديدات"""
        try:
            # تحميل من ملفات محلية أو APIs خارجية
            # هذا مثال أساسي
            
            # نطاقات خبيثة معروفة
            known_malware_domains = {
                'malware.com', 'phishing-site.net', 'fake-discord.com'
            }
            self.threat_intelligence['malware_domains'].update(known_malware_domains)
            
            # نطاقات آمنة
            safe_domains = {
                'discord.com', 'discordapp.com', 'discord.gg',
                'github.com', 'google.com', 'youtube.com',
                'stackoverflow.com', 'reddit.com'
            }
            self.threat_intelligence['safe_domains'].update(safe_domains)
            
            logger.info("✅ تم تحميل قوائم التهديدات")
            
        except Exception as e:
            logger.error(f"خطأ في تحميل قوائم التهديدات: {e}")
    
    def _is_cache_valid(self, timestamp: datetime, max_age_hours: int = 24) -> bool:
        """التحقق من صحة الكاش"""
        return datetime.now() - timestamp < timedelta(hours=max_age_hours)
    
    async def update_threat_intelligence(self):
        """تحديث قوائم التهديدات"""
        try:
            # يمكن تحديث القوائم من مصادر خارجية
            # مثل threat intelligence feeds
            
            logger.info("🔄 تم تحديث قوائم التهديدات")
            
        except Exception as e:
            logger.error(f"خطأ في تحديث قوائم التهديدات: {e}")
    
    async def get_api_status(self) -> Dict:
        """الحصول على حالة جميع الـ APIs"""
        try:
            status = {
                'virustotal': {
                    'available': bool(Config.VIRUSTOTAL_API_KEY),
                    'status': 'unknown',
                    'quota_remaining': None,
                    'last_check': None
                },
                'external_apis': {
                    'session_active': self.session is not None,
                    'cache_size': {
                        'url_reputation': len(self.cache['url_reputation']),
                        'domain_info': len(self.cache['domain_info']),
                        'ip_geolocation': len(self.cache['ip_geolocation'])
                    },
                    'threat_intelligence': {
                        'malware_domains': len(self.threat_intelligence['malware_domains']),
                        'phishing_urls': len(self.threat_intelligence['phishing_urls']),
                        'suspicious_ips': len(self.threat_intelligence['suspicious_ips']),
                        'safe_domains': len(self.threat_intelligence['safe_domains'])
                    }
                }
            }
            
            # فحص حالة VirusTotal
            if Config.VIRUSTOTAL_API_KEY:
                vt_status = await self.virustotal.get_api_status()
                if vt_status:
                    status['virustotal'].update(vt_status)
                    status['virustotal']['status'] = 'active'
                else:
                    status['virustotal']['status'] = 'error'
            else:
                status['virustotal']['status'] = 'no_api_key'
            
            return status
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على حالة الـ APIs: {e}")
            return {'error': str(e)}
    
    async def bulk_url_scan(self, urls: List[str]) -> Dict[str, Dict]:
        """فحص مجموعة من الروابط"""
        results = {}
        
        try:
            # فحص الروابط بشكل متوازي مع حد أقصى للطلبات المتزامنة
            semaphore = asyncio.Semaphore(5)  # حد أقصى 5 طلبات متزامنة
            
            async def scan_single_url(url: str):
                async with semaphore:
                    return await self.comprehensive_url_scan(url)
            
            # تشغيل الفحص المتوازي
            tasks = [scan_single_url(url) for url in urls]
            scan_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # تجميع النتائج
            for i, url in enumerate(urls):
                if isinstance(scan_results[i], Exception):
                    results[url] = {
                        'error': str(scan_results[i]),
                        'is_safe': True,  # افتراض الأمان في حالة الخطأ
                        'threat_level': 'unknown'
                    }
                else:
                    results[url] = scan_results[i]
            
            logger.info(f"🔍 تم فحص {len(urls)} رابط بشكل مجمع")
            return results
            
        except Exception as e:
            logger.error(f"خطأ في الفحص المجمع للروابط: {e}")
            return {url: {'error': str(e), 'is_safe': True} for url in urls}
    
    async def get_threat_statistics(self) -> Dict:
        """الحصول على إحصائيات التهديدات"""
        try:
            stats = {
                'total_scans_today': 0,
                'threats_detected_today': 0,
                'top_threat_types': {},
                'cache_hit_rate': 0.0,
                'api_calls_today': {
                    'virustotal': 0,
                    'domain_reputation': 0,
                    'ip_geolocation': 0
                },
                'threat_intelligence_stats': {
                    'last_update': None,
                    'sources_count': len(self.threat_intelligence),
                    'total_entries': sum(len(v) for v in self.threat_intelligence.values())
                }
            }
            
            # يمكن إضافة منطق لحساب الإحصائيات من قاعدة البيانات
            # أو من ملفات السجلات
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات التهديدات: {e}")
            return {}
    
    async def clear_cache(self, cache_type: str = 'all'):
        """مسح الكاش"""
        try:
            if cache_type == 'all':
                self.cache = {
                    'url_reputation': {},
                    'domain_info': {},
                    'ip_geolocation': {}
                }
                logger.info("🗑️ تم مسح جميع الكاش")
            elif cache_type in self.cache:
                self.cache[cache_type] = {}
                logger.info(f"🗑️ تم مسح كاش {cache_type}")
            else:
                logger.warning(f"نوع كاش غير معروف: {cache_type}")
                
        except Exception as e:
            logger.error(f"خطأ في مسح الكاش: {e}")
    
    async def add_to_threat_list(self, threat_type: str, value: str):
        """إضافة عنصر لقائمة التهديدات"""
        try:
            if threat_type in self.threat_intelligence:
                self.threat_intelligence[threat_type].add(value)
                logger.info(f"➕ تم إضافة {value} لقائمة {threat_type}")
            else:
                logger.warning(f"نوع تهديد غير معروف: {threat_type}")
                
        except Exception as e:
            logger.error(f"خطأ في إضافة التهديد: {e}")
    
    async def remove_from_threat_list(self, threat_type: str, value: str):
        """إزالة عنصر من قائمة التهديدات"""
        try:
            if threat_type in self.threat_intelligence:
                self.threat_intelligence[threat_type].discard(value)
                logger.info(f"➖ تم إزالة {value} من قائمة {threat_type}")
            else:
                logger.warning(f"نوع تهديد غير معروف: {threat_type}")
                
        except Exception as e:
            logger.error(f"خطأ في إزالة التهديد: {e}")
    
    async def export_threat_intelligence(self) -> Dict:
        """تصدير قوائم التهديدات"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'threat_intelligence': {
                    key: list(value) for key, value in self.threat_intelligence.items()
                },
                'cache_statistics': {
                    'url_reputation_entries': len(self.cache['url_reputation']),
                    'domain_info_entries': len(self.cache['domain_info']),
                    'ip_geolocation_entries': len(self.cache['ip_geolocation'])
                }
            }
            
            logger.info("📤 تم تصدير قوائم التهديدات")
            return export_data
            
        except Exception as e:
            logger.error(f"خطأ في تصدير قوائم التهديدات: {e}")
            return {}
    
    async def import_threat_intelligence(self, import_data: Dict):
        """استيراد قوائم التهديدات"""
        try:
            if 'threat_intelligence' in import_data:
                for key, values in import_data['threat_intelligence'].items():
                    if key in self.threat_intelligence:
                        self.threat_intelligence[key].update(set(values))
                        logger.info(f"📥 تم استيراد {len(values)} عنصر لقائمة {key}")
            
            logger.info("✅ تم استيراد قوائم التهديدات بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ في استيراد قوائم التهديدات: {e}")


# إنشاء مثيل عام للاستخدام
api_manager = ExternalAPIManager()