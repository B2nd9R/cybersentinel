"""
Threat Analyzer - نظام تحليل التهديدات
يقوم بتحليل وتقييم التهديدات المكتشفة من قبل الأنظمة الأخرى
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from collections import defaultdict
import json

from config import Config
from core.logger import get_security_logger
from core.database import db_manager

logger = get_security_logger()

class ThreatAnalyzer:
    """محلل التهديدات الأمنية"""
    
    def __init__(self):
        # تصنيفات التهديدات
        self.threat_categories = {
            'spam': {
                'weight': 1,
                'threshold': 5,
                'decay_time': timedelta(hours=24)
            },
            'suspicious_link': {
                'weight': 2,
                'threshold': 3,
                'decay_time': timedelta(days=7)
            },
            'raid_attempt': {
                'weight': 3,
                'threshold': 2,
                'decay_time': timedelta(days=14)
            },
            'malicious_file': {
                'weight': 4,
                'threshold': 1,
                'decay_time': timedelta(days=30)
            },
            'suspicious_behavior': {
                'weight': 2,
                'threshold': 4,
                'decay_time': timedelta(days=3)
            }
        }
        
        # ذاكرة التهديدات المؤقتة
        self.threat_memory = defaultdict(list)
        
        # قائمة التهديدات المعروفة
        self.known_threats = self._load_known_threats()
    
    def _load_known_threats(self) -> Dict:
        """تحميل قائمة التهديدات المعروفة من ملف JSON"""
        try:
            with open('data/threats.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في تحميل ملف التهديدات: {e}")
            return {}
    
    async def analyze_threat(self, threat_data: Dict) -> Dict:
        """تحليل تهديد جديد"""
        # تحديد نوع التهديد وتصنيفه
        threat_type = self._categorize_threat(threat_data)
        
        # تحليل مستوى الخطورة
        severity = await self._analyze_severity(threat_data, threat_type)
        
        # تحديث الذاكرة المؤقتة
        self._update_threat_memory(threat_data, threat_type, severity)
        
        # تحليل العلاقات مع تهديدات أخرى
        related_threats = await self._find_related_threats(threat_data)
        
        # إنشاء تقرير التحليل
        analysis_report = {
            'threat_id': threat_data.get('id'),
            'timestamp': datetime.utcnow().isoformat(),
            'type': threat_type,
            'severity': severity,
            'confidence': self._calculate_confidence(threat_data),
            'related_threats': related_threats,
            'recommendations': await self._generate_recommendations(threat_type, severity)
        }
        
        # حفظ التحليل في قاعدة البيانات
        await self._save_analysis(analysis_report)
        
        return analysis_report
    
    def _categorize_threat(self, threat_data: Dict) -> str:
        """تصنيف التهديد بناءً على خصائصه"""
        # فحص المؤشرات المختلفة
        indicators = threat_data.get('indicators', [])
        
        if 'raid' in indicators or 'mass_join' in indicators:
            return 'raid_attempt'
        
        if 'malware' in indicators or 'virus' in indicators:
            return 'malicious_file'
        
        if 'spam' in indicators or 'flood' in indicators:
            return 'spam'
        
        if 'suspicious_link' in indicators or 'phishing' in indicators:
            return 'suspicious_link'
        
        return 'suspicious_behavior'
    
    async def _analyze_severity(self, threat_data: Dict, threat_type: str) -> str:
        """تحليل مستوى خطورة التهديد"""
        # الحصول على معامل الوزن للتهديد
        weight = self.threat_categories[threat_type]['weight']
        
        # حساب النقاط الإجمالية
        total_points = 0
        
        # فحص المؤشرات
        indicators = threat_data.get('indicators', [])
        total_points += len(indicators) * weight
        
        # فحص تكرار التهديد
        repeat_count = await self._get_threat_repeat_count(threat_data)
        total_points += repeat_count * (weight / 2)
        
        # فحص مستوى الثقة
        confidence = threat_data.get('confidence', 0)
        total_points *= (confidence + 1) / 2
        
        # تحديد المستوى
        if total_points >= 15:
            return 'critical'
        elif total_points >= 10:
            return 'high'
        elif total_points >= 5:
            return 'medium'
        return 'low'
    
    def _update_threat_memory(self, threat_data: Dict, threat_type: str, severity: str):
        """تحديث ذاكرة التهديدات المؤقتة"""
        # إضافة التهديد الجديد
        self.threat_memory[threat_type].append({
            'data': threat_data,
            'severity': severity,
            'timestamp': datetime.utcnow()
        })
        
        # تنظيف التهديدات القديمة
        self._cleanup_old_threats(threat_type)
    
    def _cleanup_old_threats(self, threat_type: str):
        """تنظيف التهديدات القديمة من الذاكرة"""
        current_time = datetime.utcnow()
        decay_time = self.threat_categories[threat_type]['decay_time']
        
        self.threat_memory[threat_type] = [
            threat for threat in self.threat_memory[threat_type]
            if current_time - threat['timestamp'] < decay_time
        ]
    
    async def _find_related_threats(self, threat_data: Dict) -> List[Dict]:
        """البحث عن التهديدات المرتبطة"""
        related = []
        
        # البحث في قاعدة البيانات
        source_id = threat_data.get('source_id')
        if source_id:
            db_threats = await db_manager.get_threats_by_source(source_id)
            related.extend(db_threats)
        
        # البحث في الذاكرة المؤقتة
        for threat_type, threats in self.threat_memory.items():
            for threat in threats:
                if self._is_related(threat_data, threat['data']):
                    related.append({
                        'type': threat_type,
                        'severity': threat['severity'],
                        'timestamp': threat['timestamp'].isoformat()
                    })
        
        return related[:5]  # إرجاع أحدث 5 تهديدات مرتبطة
    
    def _is_related(self, threat1: Dict, threat2: Dict) -> bool:
        """تحديد ما إذا كان هناك علاقة بين تهديدين"""
        # فحص المصدر
        if threat1.get('source_id') == threat2.get('source_id'):
            return True
        
        # فحص المؤشرات المشتركة
        indicators1 = set(threat1.get('indicators', []))
        indicators2 = set(threat2.get('indicators', []))
        if len(indicators1.intersection(indicators2)) >= 2:
            return True
        
        return False
    
    def _calculate_confidence(self, threat_data: Dict) -> float:
        """حساب مستوى الثقة في التحليل"""
        confidence = 0.0
        factors = 0
        
        # فحص وجود مؤشرات
        if threat_data.get('indicators'):
            confidence += len(threat_data['indicators']) * 0.2
            factors += 1
        
        # فحص وجود أدلة
        if threat_data.get('evidence'):
            confidence += 0.3
            factors += 1
        
        # فحص التكرار
        if threat_data.get('repeat_count', 0) > 0:
            confidence += 0.25
            factors += 1
        
        # حساب المتوسط
        return min(confidence / max(factors, 1), 1.0)
    
    async def _generate_recommendations(self, threat_type: str, severity: str) -> List[str]:
        """توليد توصيات للتعامل مع التهديد"""
        recommendations = []
        
        if severity in ['critical', 'high']:
            recommendations.append("اتخاذ إجراء فوري لمنع التهديد")
            
            if threat_type == 'raid_attempt':
                recommendations.extend([
                    "تفعيل وضع الحماية المشددة",
                    "مراجعة إعدادات الأمان للسيرفر",
                    "تقييد انضمام الأعضاء الجدد مؤقتاً"
                ])
            
            elif threat_type == 'malicious_file':
                recommendations.extend([
                    "حذف الملف المشبوه فوراً",
                    "فحص السيرفر بحثاً عن ملفات مشابهة",
                    "تحديث قائمة الملفات المحظورة"
                ])
        
        elif severity == 'medium':
            recommendations.append("مراقبة الوضع عن كثب")
            
            if threat_type == 'suspicious_behavior':
                recommendations.extend([
                    "تسجيل نشاط المستخدم المشبوه",
                    "مراجعة صلاحيات المستخدم"
                ])
        
        else:  # low
            recommendations.append("توثيق التهديد للمراجعة المستقبلية")
        
        return recommendations
    
    async def _save_analysis(self, analysis: Dict):
        """حفظ نتائج التحليل في قاعدة البيانات"""
        try:
            await db_manager.save_threat_analysis(analysis)
            logger.info(f"تم حفظ تحليل التهديد {analysis['threat_id']}")
        except Exception as e:
            logger.error(f"خطأ في حفظ تحليل التهديد: {e}")
    
    async def _get_threat_repeat_count(self, threat_data: Dict) -> int:
        """حساب عدد مرات تكرار نفس التهديد"""
        source_id = threat_data.get('source_id')
        if not source_id:
            return 0
        
        try:
            return await db_manager.get_threat_repeat_count(source_id)
        except Exception as e:
            logger.error(f"خطأ في حساب تكرار التهديد: {e}")
            return 0