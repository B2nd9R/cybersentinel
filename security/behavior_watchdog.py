"""
Behavior Watchdog - نظام مراقبة السلوك المشبوه
يراقب سلوك المستخدمين ويكتشف الأنماط المشبوهة
"""

import asyncio
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import discord

from config import Config
from core.logger import get_security_logger
from core.database import db_manager

logger = get_security_logger()

class BehaviorWatchdog:
    """نظام مراقبة السلوك المشبوه"""
    
    def __init__(self):
        # تتبع نشاط المستخدمين
        self.user_activity = defaultdict(lambda: {
            'messages': deque(maxlen=50),
            'channels': set(),
            'danger_points': 0,
            'last_warning': None,
            'violations': []
        })
        
        # تتبع الرسائل المتطابقة
        self.duplicate_messages = defaultdict(list)
        
        # تتبع الكلمات المفتاحية المشبوهة
        self.suspicious_patterns = [
            r'(?i)(free\s+nitro|discord\s+gift)',
            r'(?i)(click\s+here|claim\s+now)',
            r'(?i)(verify\s+account|suspended)',
            r'(?i)(congratulations|you\s+won)',
            r'(?i)(limited\s+time|act\s+fast)',
            r'(?i)(free\s+bitcoin|crypto\s+giveaway)',
            r'(?i)(password|login\s+here)',
            r'(?i)(urgent\s+action|immediate)',
        ]
        
        # نقاط الخطر لكل نوع انتهاك
        self.violation_points = {
            'spam': 3,
            'suspicious_keywords': 5,
            'duplicate_messages': 4,
            'rapid_posting': 2,
            'channel_hopping': 3,
            'suspicious_links': 7,
            'mass_mentions': 6,
            'encoded_content': 4
        }
    
    async def analyze_message(self, message: discord.Message) -> Dict:
        """تحليل رسالة للكشف عن السلوك المشبوه"""
        if message.author.bot:
            return {'is_suspicious': False}
        
        user_id = message.author.id
        guild_id = message.guild.id if message.guild else None
        
        analysis = {
            'is_suspicious': False,
            'violations': [],
            'danger_points': 0,
            'recommended_action': 'none'
        }
        
        # تحديث نشاط المستخدم
        await self._update_user_activity(message)
        
        # فحص الانتهاكات المختلفة
        violations = []
        
        # 1. فحص الكلمات المفتاحية المشبوهة
        suspicious_keywords = await self._check_suspicious_keywords(message)
        if suspicious_keywords:
            violations.extend(suspicious_keywords)
        
        # 2. فحص الرسائل المكررة
        duplicate_check = await self._check_duplicate_messages(message)
        if duplicate_check:
            violations.append(duplicate_check)
        
        # 3. فحص النشر السريع
        rapid_posting = await self._check_rapid_posting(message)
        if rapid_posting:
            violations.append(rapid_posting)
        
        # 4. فحص التنقل بين القنوات
        channel_hopping = await self._check_channel_hopping(message)
        if channel_hopping:
            violations.append(channel_hopping)
        
        # 5. فحص الإشارات الجماعية
        mass_mentions = await self._check_mass_mentions(message)
        if mass_mentions:
            violations.append(mass_mentions)
        
        # 6. فحص المحتوى المشفر
        encoded_content = await self._check_encoded_content(message)
        if encoded_content:
            violations.append(encoded_content)
        
        # حساب نقاط الخطر الإجمالية
        total_points = sum(v.get('points', 0) for v in violations)
        
        if violations:
            analysis.update({
                'is_suspicious': True,
                'violations': violations,
                'danger_points': total_points,
                'recommended_action': await self._determine_action(user_id, guild_id, total_points)
            })
            
            # تسجيل في قاعدة البيانات
            await self._log_violations(message, violations, total_points)
        
        return analysis
    
    async def _update_user_activity(self, message: discord.Message):
        """تحديث نشاط المستخدم"""
        user_id = message.author.id
        activity = self.user_activity[user_id]
        
        activity['messages'].append({
            'content': message.content,
            'timestamp': message.created_at,
            'channel_id': message.channel.id,
            'message_id': message.id
        })
        
        activity['channels'].add(message.channel.id)
    
    async def _check_suspicious_keywords(self, message: discord.Message) -> List[Dict]:
        """فحص الكلمات المفتاحية المشبوهة"""
        violations = []
        content = message.content.lower()
        
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, content)
            if matches:
                violations.append({
                    'type': 'suspicious_keywords',
                    'pattern': pattern,
                    'matches': matches,
                    'points': self.violation_points['suspicious_keywords'],
                    'severity': 'high'
                })
        
        # فحص الكلمات المفتاحية من الإعدادات
        for keyword in Config.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in content:
                violations.append({
                    'type': 'suspicious_keywords',
                    'keyword': keyword,
                    'points': self.violation_points['suspicious_keywords'],
                    'severity': 'medium'
                })
        
        return violations
    
    async def _check_duplicate_messages(self, message: discord.Message) -> Optional[Dict]:
        """فحص الرسائل المكررة"""
        content_hash = hash(message.content.lower().strip())
        user_id = message.author.id
        
        # إضافة الرسالة للتتبع
        self.duplicate_messages[content_hash].append({
            'user_id': user_id,
            'timestamp': message.created_at,
            'channel_id': message.channel.id
        })
        
        # فحص الرسائل المكررة في آخر 10 دقائق
        recent_threshold = datetime.now() - timedelta(minutes=10)
        recent_duplicates = [
            msg for msg in self.duplicate_messages[content_hash]
            if msg['timestamp'] > recent_threshold and msg['user_id'] == user_id
        ]
        
        if len(recent_duplicates) >= 3:
            return {
                'type': 'duplicate_messages',
                'count': len(recent_duplicates),
                'points': self.violation_points['duplicate_messages'],
                'severity': 'medium'
            }
        
        return None
    
    async def _check_rapid_posting(self, message: discord.Message) -> Optional[Dict]:
        """فحص النشر السريع"""
        user_id = message.author.id
        activity = self.user_activity[user_id]
        
        # فحص آخر دقيقة
        recent_threshold = datetime.now() - timedelta(minutes=1)
        recent_messages = [
            msg for msg in activity['messages']
            if msg['timestamp'] > recent_threshold
        ]
        
        if len(recent_messages) > Config.MAX_MESSAGES_PER_MINUTE:
            return {
                'type': 'rapid_posting',
                'count': len(recent_messages),
                'points': self.violation_points['rapid_posting'],
                'severity': 'medium'
            }
        
        return None
    
    async def _check_channel_hopping(self, message: discord.Message) -> Optional[Dict]:
        """فحص التنقل السريع بين القنوات"""
        user_id = message.author.id
        activity = self.user_activity[user_id]
        
        # فحص آخر 5 دقائق
        recent_threshold = datetime.now() - timedelta(minutes=5)
        recent_channels = set()
        
        for msg in activity['messages']:
            if msg['timestamp'] > recent_threshold:
                recent_channels.add(msg['channel_id'])
        
        if len(recent_channels) >= 5:
            return {
                'type': 'channel_hopping',
                'channels_count': len(recent_channels),
                'points': self.violation_points['channel_hopping'],
                'severity': 'medium'
            }
        
        return None
    
    async def _check_mass_mentions(self, message: discord.Message) -> Optional[Dict]:
        """فحص الإشارات الجماعية"""
        mention_count = len(message.mentions) + len(message.role_mentions)
        
        if mention_count >= 5:
            return {
                'type': 'mass_mentions',
                'count': mention_count,
                'points': self.violation_points['mass_mentions'],
                'severity': 'high'
            }
        
        return None
    
    async def _check_encoded_content(self, message: discord.Message) -> Optional[Dict]:
        """فحص المحتوى المشفر أو المشبوه"""
        content = message.content
        
        # فحص Base64
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        if re.search(base64_pattern, content):
            return {
                'type': 'encoded_content',
                'encoding': 'base64',
                'points': self.violation_points['encoded_content'],
                'severity': 'medium'
            }
        
        # فحص النصوص المشفرة الأخرى
        if len(content) > 50 and content.count(' ') / len(content) < 0.1:
            return {
                'type': 'encoded_content',
                'encoding': 'unknown',
                'points': self.violation_points['encoded_content'],
                'severity': 'low'
            }
        
        return None
    
    async def _determine_action(self, user_id: int, guild_id: int, points: int) -> str:
        """تحديد الإجراء المطلوب بناءً على نقاط الخطر"""
        # الحصول على نقاط الخطر الحالية من قاعدة البيانات
        current_score = await db_manager.get_user_danger_score(guild_id, user_id)
        total_points = current_score.get('danger_points', 0) + points
        
        if total_points >= Config.MAX_DANGER_POINTS:
            return 'ban'
        elif total_points >= Config.MAX_DANGER_POINTS * 0.8:
            return 'timeout'
        elif total_points >= Config.MAX_DANGER_POINTS * 0.5:
            return 'warn'
        else:
            return 'monitor'
    
    async def _log_violations(self, message: discord.Message, violations: List[Dict], total_points: int):
        """تسجيل الانتهاكات في قاعدة البيانات"""
        guild_id = message.guild.id if message.guild else None
        user_id = message.author.id
        
        # تسجيل التهديد
        violation_summary = ', '.join([v['type'] for v in violations])
        await db_manager.add_threat(
            guild_id=guild_id,
            user_id=user_id,
            threat_type='behavior_violation',
            content=f"Violations: {violation_summary} | Points: {total_points}",
            severity='medium' if total_points < 10 else 'high'
        )
        
        # إضافة نقاط الخطر
        await db_manager.add_danger_points(guild_id, user_id, total_points)
        
        logger.warning(
            f"🚨 سلوك مشبوه من المستخدم {user_id} في السيرفر {guild_id}: "
            f"{violation_summary} ({total_points} نقاط)"
        )
    
    async def get_user_behavior_report(self, user_id: int, guild_id: int) -> Dict:
        """الحصول على تقرير سلوك المستخدم"""
        # الحصول على البيانات من قاعدة البيانات
        danger_score = await db_manager.get_user_danger_score(guild_id, user_id)
        recent_threats = await db_manager.get_user_threats(guild_id, user_id, days=30)
        
        # تحليل النشاط الحالي
        activity = self.user_activity.get(user_id, {})
        
        return {
            'user_id': user_id,
            'guild_id': guild_id,
            'danger_points': danger_score.get('danger_points', 0),
            'total_warnings': danger_score.get('total_warnings', 0),
            'recent_threats': len(recent_threats),
            'active_channels': len(activity.get('channels', set())),
            'recent_messages': len(activity.get('messages', [])),
            'last_violation': danger_score.get('last_violation'),
            'status': danger_score.get('status', 'active')
        }
    
    async def reset_user_score(self, user_id: int, guild_id: int):
        """إعادة تعيين نقاط المستخدم"""
        await db_manager.add_danger_points(guild_id, user_id, -999)  # إعادة تعيين
        
        # مسح النشاط المحلي
        if user_id in self.user_activity:
            del self.user_activity[user_id]
        
        logger.info(f"تم إعادة تعيين نقاط المستخدم {user_id} في السيرفر {guild_id}")
    
    def cleanup_old_data(self):
        """تنظيف البيانات القديمة من الذاكرة"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # تنظيف الرسائل المكررة
        for content_hash in list(self.duplicate_messages.keys()):
            self.duplicate_messages[content_hash] = [
                msg for msg in self.duplicate_messages[content_hash]
                if msg['timestamp'] > cutoff_time
            ]
            
            if not self.duplicate_messages[content_hash]:
                del self.duplicate_messages[content_hash]
        
        # تنظيف نشاط المستخدمين
        for user_id in list(self.user_activity.keys()):
            activity = self.user_activity[user_id]
            old_messages = activity['messages']
            activity['messages'] = deque(
                [msg for msg in old_messages if msg['timestamp'] > cutoff_time],
                maxlen=50
            )
            
            if not activity['messages']:
                del self.user_activity[user_id]