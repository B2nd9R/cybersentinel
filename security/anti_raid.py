"""
Anti-Raid System - نظام مكافحة الهجمات الجماعية
يحمي السيرفر من الهجمات المنسقة والانضمام الجماعي المشبوه
"""

import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set
import discord

from config import Config
from core.logger import get_security_logger
from core.database import db_manager

logger = get_security_logger()

class AntiRaidSystem:
    """نظام الحماية من الهجمات الجماعية"""
    
    def __init__(self):
        # تتبع الانضمامات الحديثة لكل سيرفر
        self.recent_joins = defaultdict(lambda: deque(maxlen=100))
        
        # تتبع المستخدمين المشبوهين
        self.suspicious_users = defaultdict(set)
        
        # إعدادات الحماية
        self.raid_thresholds = {
            'low': {'joins_per_minute': 5, 'action': 'monitor'},
            'medium': {'joins_per_minute': 10, 'action': 'alert'},
            'high': {'joins_per_minute': 20, 'action': 'lockdown'}
        }
        
        # حالة القفل لكل سيرفر
        self.lockdown_status = defaultdict(lambda: False)
        
        # قائمة الحسابات المستثناة
        self.whitelist = set()
    
    async def process_member_join(self, member: discord.Member) -> Dict:
        """معالجة انضمام عضو جديد"""
        guild_id = member.guild.id
        current_time = datetime.utcnow()
        
        # تحديث سجل الانضمامات
        self.recent_joins[guild_id].append({
            'member_id': member.id,
            'timestamp': current_time,
            'account_age': (current_time - member.created_at).days
        })
        
        # تحليل نمط الانضمام
        analysis = await self._analyze_join_pattern(guild_id)
        
        # فحص مؤشرات الخطر
        risk_factors = await self._check_risk_factors(member)
        
        # تحديد الإجراء المناسب
        action = await self._determine_action(guild_id, analysis, risk_factors)
        
        # تنفيذ الإجراء
        await self._execute_action(member.guild, action)
        
        return {
            'is_raid': analysis['is_raid'],
            'risk_level': analysis['risk_level'],
            'risk_factors': risk_factors,
            'action_taken': action
        }
    
    async def _analyze_join_pattern(self, guild_id: int) -> Dict:
        """تحليل نمط الانضمام للكشف عن الهجمات"""
        recent = self.recent_joins[guild_id]
        if not recent:
            return {'is_raid': False, 'risk_level': 'low'}
        
        # حساب معدل الانضمام في الدقيقة
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        joins_last_minute = sum(1 for j in recent if j['timestamp'] > one_minute_ago)
        
        # تحليل نمط الحسابات
        new_accounts = sum(1 for j in recent if j['account_age'] < 7)
        
        # تحديد مستوى الخطر
        risk_level = 'low'
        is_raid = False
        
        for level, threshold in self.raid_thresholds.items():
            if joins_last_minute >= threshold['joins_per_minute']:
                risk_level = level
                is_raid = True
        
        return {
            'is_raid': is_raid,
            'risk_level': risk_level,
            'joins_per_minute': joins_last_minute,
            'new_accounts_ratio': new_accounts / len(recent) if recent else 0
        }
    
    async def _check_risk_factors(self, member: discord.Member) -> List[str]:
        """فحص عوامل الخطر للعضو الجديد"""
        risk_factors = []
        
        # فحص عمر الحساب
        account_age = (datetime.utcnow() - member.created_at).days
        if account_age < 7:
            risk_factors.append('new_account')
        
        # فحص الصورة الشخصية
        if not member.avatar:
            risk_factors.append('default_avatar')
        
        # فحص اسم المستخدم
        if any(char in member.name for char in Config.SUSPICIOUS_CHARACTERS):
            risk_factors.append('suspicious_username')
        
        return risk_factors
    
    async def _determine_action(self, guild_id: int, analysis: Dict, risk_factors: List[str]) -> str:
        """تحديد الإجراء المناسب بناءً على التحليل"""
        if analysis['is_raid']:
            if analysis['risk_level'] == 'high':
                return 'lockdown'
            elif analysis['risk_level'] == 'medium':
                return 'alert'
        
        if len(risk_factors) >= 2:
            return 'monitor'
        
        return 'none'
    
    async def _execute_action(self, guild: discord.Guild, action: str):
        """تنفيذ الإجراء الأمني"""
        if action == 'lockdown' and not self.lockdown_status[guild.id]:
            await self._enable_lockdown(guild)
        
        elif action == 'alert':
            await self._send_alert(guild)
        
        elif action == 'monitor':
            await self._update_monitoring(guild)
    
    async def _enable_lockdown(self, guild: discord.Guild):
        """تفعيل وضع القفل للحماية"""
        self.lockdown_status[guild.id] = True
        
        try:
            # تعديل إعدادات السيرفر للحماية
            await guild.edit(verification_level=discord.VerificationLevel.high)
            
            # إرسال تنبيه للإدارة
            log_channel = await self._get_log_channel(guild)
            if log_channel:
                embed = discord.Embed(
                    title="🚨 تم تفعيل وضع الحماية",
                    description="تم اكتشاف هجوم محتمل. تم رفع مستوى الحماية تلقائياً.",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)
            
            # تسجيل الحدث
            logger.warning(f"تم تفعيل وضع الحماية في السيرفر {guild.name} (ID: {guild.id})")
            
            # جدولة إيقاف وضع القفل بعد فترة
            asyncio.create_task(self._schedule_lockdown_disable(guild))
            
        except discord.Forbidden:
            logger.error(f"لا توجد صلاحيات كافية لتفعيل وضع الحماية في السيرفر {guild.id}")
    
    async def _schedule_lockdown_disable(self, guild: discord.Guild):
        """جدولة إيقاف وضع القفل"""
        await asyncio.sleep(Config.LOCKDOWN_DURATION)
        if self.lockdown_status[guild.id]:
            await self._disable_lockdown(guild)
    
    async def _disable_lockdown(self, guild: discord.Guild):
        """إيقاف وضع القفل"""
        self.lockdown_status[guild.id] = False
        
        try:
            # إعادة الإعدادات لوضعها الطبيعي
            await guild.edit(verification_level=discord.VerificationLevel.low)
            
            # إرسال تنبيه
            log_channel = await self._get_log_channel(guild)
            if log_channel:
                embed = discord.Embed(
                    title="✅ تم إيقاف وضع الحماية",
                    description="تم إعادة إعدادات الحماية لوضعها الطبيعي.",
                    color=discord.Color.green()
                )
                await log_channel.send(embed=embed)
            
            logger.info(f"تم إيقاف وضع الحماية في السيرفر {guild.name} (ID: {guild.id})")
            
        except discord.Forbidden:
            logger.error(f"لا توجد صلاحيات كافية لإيقاف وضع الحماية في السيرفر {guild.id}")
    
    async def _send_alert(self, guild: discord.Guild):
        """إرسال تنبيه للإدارة"""
        log_channel = await self._get_log_channel(guild)
        if log_channel:
            embed = discord.Embed(
                title="⚠️ تنبيه أمني",
                description="تم رصد نشاط مشبوه في الانضمامات الجديدة.",
                color=discord.Color.gold()
            )
            await log_channel.send(embed=embed)
    
    async def _update_monitoring(self, guild: discord.Guild):
        """تحديث حالة المراقبة"""
        # تحديث قاعدة البيانات بالإحصائيات
        stats = {
            'guild_id': guild.id,
            'timestamp': datetime.utcnow(),
            'joins_count': len(self.recent_joins[guild.id]),
            'suspicious_count': len(self.suspicious_users[guild.id])
        }
        await db_manager.update_security_stats(stats)
    
    async def _get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """الحصول على قناة السجلات"""
        # البحث عن قناة السجلات في الإعدادات
        log_channel_id = await db_manager.get_guild_setting(guild.id, 'log_channel_id')
        if log_channel_id:
            return guild.get_channel(log_channel_id)
        return None