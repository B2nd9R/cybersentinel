import discord
import asyncio
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from core.logger import get_security_logger, log_security_event, log_threat_detected
from core.database import db_manager
from config import Config

logger = get_security_logger()

class EventHandler:
    """معالج أحداث البوت"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # تسجيل معالجات الأحداث
        self._register_events()
        
        # متغيرات تتبع النشاط
        self.message_cache = {}  # تخزين مؤقت للرسائل لاكتشاف التكرار
        self.user_activity = defaultdict(list)  # تتبع معدل نشاط المستخدمين
        self.join_tracker = defaultdict(list)  # تتبع الانضمامات لكشف الهجمات
        
        # إعدادات الكشف
        self.spam_threshold = 5  # عدد الرسائل المكررة
        self.spam_window = 30    # النافزة الزمنية بالثواني
        self.activity_threshold = Config.MAX_MESSAGES_PER_MINUTE
        
        # أنماط الروابط
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # الكلمات المشبوهة
        self.suspicious_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in Config.SUSPICIOUS_KEYWORDS
        ]
        
    def _register_events(self):
        """تسجيل معالجات الأحداث"""
        self.bot.add_listener(self.on_message, 'on_message')
        self.bot.add_listener(self.on_message_edit, 'on_message_edit')
        self.bot.add_listener(self.on_message_delete, 'on_message_delete')
        self.bot.add_listener(self.on_member_join, 'on_member_join')
        self.bot.add_listener(self.on_member_remove, 'on_member_remove')
        self.bot.add_listener(self.on_member_update, 'on_member_update')
        self.bot.add_listener(self.on_guild_join, 'on_guild_join')
        self.bot.add_listener(self.on_error, 'on_error')
    
    async def on_message(self, message: discord.Message):
        """معالج الرسائل الجديدة"""
        # تجاهل رسائل البوت
        if message.author.bot:
            return
        
        # تجاهل الرسائل الخاصة
        if not message.guild:
            return
        
        try:
            # الحصول على إعدادات السيرفر
            guild_settings = await db_manager.get_guild_settings(message.guild.id)
            
            # تحديث نشاط المستخدم
            await self._track_user_activity(message)
            
            # فحص الروابط
            if guild_settings.get('link_scan_enabled', True):
                await self._scan_message_links(message)
            
            # مراقبة السلوك
            if guild_settings.get('behavior_monitoring', True):
                await self._monitor_behavior(message)
            
            # فحص المحتوى المشبوه
            await self._scan_suspicious_content(message)
            
            # فحص الملفات المرفقة
            if message.attachments:
                await self._scan_attachments(message)
            
            # فحص التكرار والسبام
            await self._check_spam(message)
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الرسالة: {e}")
    
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """معالج تعديل الرسائل"""
        # تجاهل رسائل البوت
        if after.author.bot or not after.guild:
            return
        
        try:
            # إذا تم إضافة رابط في التعديل، افحصه
            if not self._has_links(before.content) and self._has_links(after.content):
                await self._scan_message_links(after)
            
            # تسجيل التعديلات المشبوهة
            if self._is_suspicious_edit(before, after):
                await self._log_suspicious_edit(before, after)
                
        except Exception as e:
            logger.error(f"خطأ في معالجة تعديل الرسالة: {e}")
    
    async def on_message_delete(self, message: discord.Message):
        """معالج حذف الرسائل"""
        if message.author.bot or not message.guild:
            return
        
        # تسجيل حذف الرسائل المشبوهة
        if self._is_suspicious_content(message.content):
            log_security_event(
                "SUSPICIOUS_DELETE", 
                message.author.id, 
                message.guild.id,
                f"Deleted suspicious message: {message.content[:100]}"
            )
    
    async def on_member_join(self, member: discord.Member):
        """معالج انضمام عضو جديد"""
        try:
            # تتبع الانضمامات للكشف عن الهجمات
            await self._track_member_join(member)
            
            # فحص مكافحة الهجمات
            if self.bot.anti_raid:
                await self.bot.anti_raid.check_member_join(member)
            
            # فحص الحساب الجديد
            await self._check_new_account(member)
            
            # فحص الاسم المشبوه
            if self._is_suspicious_name(member.display_name):
                await self._handle_suspicious_name(member)
            
            # إرسال رسالة ترحيب أمنية
            await self._send_security_welcome(member)
            
        except Exception as e:
            logger.error(f"خطأ في معالجة انضمام العضو: {e}")
    
    async def on_member_remove(self, member: discord.Member):
        """معالج مغادرة عضو"""
        logger.info(f"غادر العضو {member.name} السيرفر {member.guild.name}")
        
        # تنظيف بيانات المستخدم من التتبع المؤقت
        user_key = f"{member.guild.id}_{member.id}"
        if user_key in self.user_activity:
            del self.user_activity[user_key]
    
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """معالج تحديث بيانات العضو"""
        # فحص تغيير الاسم المشبوه
        if before.display_name != after.display_name:
            if self._is_suspicious_name(after.display_name):
                await self._handle_suspicious_name(after)
    
    async def on_error(self, event: str, *args, **kwargs):
        """معالج الأخطاء العامة"""
        logger.error(f"خطأ في الحدث {event}: {args}")
    
    # وظائف المساعدة الرئيسية
    async def _track_user_activity(self, message: discord.Message):
        """تتبع نشاط المستخدم"""
        user_id = message.author.id
        guild_id = message.guild.id
        now = datetime.now()
        
        # مفتاح فريد للمستخدم في السيرفر
        user_key = f"{guild_id}_{user_id}"
        
        # إضافة النشاط الحالي
        self.user_activity[user_key].append(now)
        
        # تنظيف النشاطات القديمة (أكبر من دقيقة)
        cutoff = now - timedelta(minutes=1)
        self.user_activity[user_key] = [
            activity for activity in self.user_activity[user_key] 
            if activity > cutoff
        ]
        
        # فحص معدل النشاط
        activity_count = len(self.user_activity[user_key])
        if activity_count > self.activity_threshold:
            await self._handle_high_activity(message.author, message.guild, activity_count)
    
    async def _scan_message_links(self, message: discord.Message):
        """فحص الروابط في الرسالة"""
        urls = self.url_pattern.findall(message.content)
        
        for url in urls:
            try:
                # فحص الرابط مع نظام حماية الروابط
                if self.bot.link_guardian:
                    scan_result = await self.bot.link_guardian.scan_url(url)
                    
                    if scan_result.get('is_malicious', False):
                        await self._handle_malicious_link(message, url, scan_result)
                        
                        # تحديث الإحصائيات
                        self.bot.stats['threats_blocked'] += 1
                        
            except Exception as e:
                logger.error(f"خطأ في فحص الرابط {url}: {e}")
    
    async def _monitor_behavior(self, message: discord.Message):
        """مراقبة السلوك العام"""
        if self.bot.behavior_watchdog:
            try:
                # تحليل السلوك
                behavior_analysis = await self.bot.behavior_watchdog.analyze_message(
                    message.author.id, 
                    message.guild.id, 
                    message.content
                )
                
                # إذا كان السلوك مشبوه
                if behavior_analysis.get('is_suspicious', False):
                    await self._handle_suspicious_behavior(message, behavior_analysis)
                    
            except Exception as e:
                logger.error(f"خطأ في مراقبة السلوك: {e}")
    
    async def _scan_suspicious_content(self, message: discord.Message):
        """فحص المحتوى المشبوه"""
        content = message.content.lower()
        
        # فحص الكلمات المشبوهة
        for pattern in self.suspicious_patterns:
            if pattern.search(content):
                await self._handle_suspicious_content(message, pattern.pattern)
                break
        
        # فحص الرسائل المشفرة أو الغريبة
        if self._is_encoded_message(content):
            await self._handle_encoded_message(message)
        
        # فحص الإشارات المشبوهة
        if self._has_suspicious_mentions(message):
            await self._handle_suspicious_mentions(message)
    
    async def _scan_attachments(self, message: discord.Message):
        """فحص الملفات المرفقة"""
        for attachment in message.attachments:
            try:
                # فحص امتداد الملف
                file_ext = attachment.filename.split('.')[-1].lower()
                
                if f'.{file_ext}' in Config.DANGEROUS_FILE_EXTENSIONS:
                    await self._handle_dangerous_file(message, attachment)
                
                # فحص حجم الملف المشبوه
                if attachment.size > 50 * 1024 * 1024:  # 50MB
                    await self._handle_large_file(message, attachment)
                    
            except Exception as e:
                logger.error(f"خطأ في فحص الملف المرفق: {e}")
    
    async def _check_spam(self, message: discord.Message):
        """فحص التكرار والسبام"""
        # إنشاء هاش للرسالة
        message_hash = hashlib.md5(message.content.encode()).hexdigest()
        user_id = message.author.id
        guild_id = message.guild.id
        now = datetime.now()
        
        # مفتاح المستخدم في السيرفر
        user_key = f"{guild_id}_{user_id}"
        
        # إضافة الرسالة للكاش
        if user_key not in self.message_cache:
            self.message_cache[user_key] = []
        
        self.message_cache[user_key].append({
            'hash': message_hash,
            'timestamp': now,
            'message_id': message.id
        })
        
        # تنظيف الرسائل القديمة
        cutoff = now - timedelta(seconds=self.spam_window)
        self.message_cache[user_key] = [
            msg for msg in self.message_cache[user_key] 
            if msg['timestamp'] > cutoff
        ]
        
        # فحص التكرار
        same_messages = [
            msg for msg in self.message_cache[user_key] 
            if msg['hash'] == message_hash
        ]
        
        if len(same_messages) >= self.spam_threshold:
            await self._handle_spam_detected(message, len(same_messages))
    
    async def _track_member_join(self, member: discord.Member):
        """تتبع انضمام الأعضاء للكشف عن الهجمات"""
        guild_id = member.guild.id
        now = datetime.now()
        
        # إضافة الانضمام للتتبع
        self.join_tracker[guild_id].append(now)
        
        # تنظيف الانضمامات القديمة
        cutoff = now - timedelta(seconds=Config.RAID_DETECTION_WINDOW)
        self.join_tracker[guild_id] = [
            join_time for join_time in self.join_tracker[guild_id] 
            if join_time > cutoff
        ]
        
        # فحص معدل الانضمام
        recent_joins = len(self.join_tracker[guild_id])
        if recent_joins >= Config.RAID_DETECTION_THRESHOLD:
            await self._handle_potential_raid(member.guild, recent_joins)
    
    # معالجات التهديدات
    async def _handle_malicious_link(self, message: discord.Message, url: str, scan_result: dict):
        """معالجة الرابط الخبيث"""
        try:
            # حذف الرسالة
            await message.delete()
            
            # تسجيل التهديد
            await db_manager.add_threat(
                message.guild.id,
                message.author.id,
                "malicious_link",
                f"URL: {url}",
                "high"
            )
            
            # إضافة نقاط خطر
            await db_manager.add_danger_points(
                message.guild.id,
                message.author.id,
                5
            )
            
            # إرسال تحذير
            embed = discord.Embed(
                title="🚨 رابط خبيث محجوب",
                description=f"تم اكتشاف وحجب رابط خبيث من {message.author.mention}",
                color=Config.COLORS['error']
            )
            embed.add_field(name="الرابط", value=f"||{url}||", inline=False)
            embed.add_field(name="سبب الحجب", value=scan_result.get('reason', 'غير محدد'), inline=False)
            
            await message.channel.send(embed=embed, delete_after=10)
            
            # إرسال تنبيه للإدارة
            await self.bot.send_security_alert(message.guild.id, embed)
            
            log_threat_detected("MALICIOUS_LINK", message.author.id, message.guild.id, url)
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الرابط الخبيث: {e}")
    
    async def _handle_suspicious_behavior(self, message: discord.Message, analysis: dict):
        """معالجة السلوك المشبوه"""
        # إضافة نقاط خطر
        danger_points = analysis.get('danger_level', 2)
        await db_manager.add_danger_points(
            message.guild.id,
            message.author.id,
            danger_points
        )
        
        # تسجيل التهديد
        await db_manager.add_threat(
            message.guild.id,
            message.author.id,
            "suspicious_behavior",
            analysis.get('reason', 'سلوك مشبوه'),
            "medium"
        )
        
        log_security_event(
            "SUSPICIOUS_BEHAVIOR",
            message.author.id,
            message.guild.id,
            analysis.get('reason', 'Unknown')
        )
    
    async def _handle_spam_detected(self, message: discord.Message, count: int):
        """معالجة السبام المكتشف"""
        try:
            # حذف الرسائل المكررة
            messages_to_delete = []
            async for msg in message.channel.history(limit=50):
                if (msg.author.id == message.author.id and 
                    msg.content == message.content):
                    messages_to_delete.append(msg)
                    if len(messages_to_delete) >= count:
                        break
            
            await message.channel.delete_messages(messages_to_delete)
            
            # إضافة نقاط خطر
            await db_manager.add_danger_points(
                message.guild.id,
                message.author.id,
                3
            )
            
            # تسجيل التهديد
            await db_manager.add_threat(
                message.guild.id,
                message.author.id,
                "spam",
                f"تكرار الرسالة {count} مرات",
                "medium"
            )
            
            # إرسال تحذير
            embed = discord.Embed(
                title="⚠️ تم اكتشاف سبام",
                description=f"تم حذف {len(messages_to_delete)} رسالة مكررة من {message.author.mention}",
                color=Config.COLORS['warning']
            )
            
            warning_msg = await message.channel.send(embed=embed, delete_after=5)
            
            log_threat_detected("SPAM", message.author.id, message.guild.id, f"Count: {count}")
            
        except Exception as e:
            logger.error(f"خطأ في معالجة السبام: {e}")
    
    async def _handle_high_activity(self, user: discord.Member, guild: discord.Guild, activity_count: int):
        """معالجة النشاط المرتفع"""
        # تحذير المستخدم
        try:
            embed = discord.Embed(
                title="⚠️ تحذير: نشاط مرتفع",
                description=f"يرجى تقليل معدل الرسائل ({activity_count} رسالة في الدقيقة)",
                color=Config.COLORS['warning']
            )
            
            await user.send(embed=embed)
            
            # إضافة نقطة خطر واحدة
            await db_manager.add_danger_points(guild.id, user.id, 1)
            
            log_security_event(
                "HIGH_ACTIVITY",
                user.id,
                guild.id,
                f"Activity: {activity_count} messages/minute"
            )
            
        except discord.Forbidden:
            # لا يمكن إرسال رسالة خاصة
            pass
    
    # وظائف الفحص المساعدة
    def _has_links(self, content: str) -> bool:
        """فحص وجود روابط في النص"""
        return bool(self.url_pattern.search(content))
    
    def _is_suspicious_content(self, content: str) -> bool:
        """فحص المحتوى المشبوه"""
        if not content:
            return False
        
        content_lower = content.lower()
        return any(pattern.search(content_lower) for pattern in self.suspicious_patterns)
    
    def _is_suspicious_edit(self, before: discord.Message, after: discord.Message) -> bool:
        """فحص التعديل المشبوه"""
        # إضافة رابط بعد التعديل
        if not self._has_links(before.content) and self._has_links(after.content):
            return True
        
        # تغيير كبير في المحتوى
        if len(after.content) > len(before.content) * 2:
            return True
        
        # إضافة كلمات مشبوهة
        if (not self._is_suspicious_content(before.content) and 
            self._is_suspicious_content(after.content)):
            return True
        
        return False
    
    def _is_suspicious_name(self, name: str) -> bool:
        """فحص الاسم المشبوه"""
        if not name:
            return False
        
        suspicious_patterns = [
            r'discord\.gg',
            r'nitro',
            r'admin',
            r'mod',
            r'bot',
            r'^.{1,2}$',  # أسماء قصيرة جداً
            r'[^\w\s\u0600-\u06FF]'  # رموز غريبة (عدا العربية والإنجليزية)
        ]
        
        name_lower = name.lower()
        return any(re.search(pattern, name_lower) for pattern in suspicious_patterns)
    
    def _is_encoded_message(self, content: str) -> bool:
        """فحص الرسائل المشفرة"""
        # رسائل Base64 مشبوهة
        if len(content) > 50 and content.replace(' ', '').isalnum():
            try:
                import base64
                base64.b64decode(content)
                return True
            except:
                pass
        
        # رسائل بها رموز غريبة كثيرة
        special_chars = sum(1 for char in content if not char.isalnum() and not char.isspace())
        if special_chars > len(content) * 0.3:
            return True
        
        return False
    
    def _has_suspicious_mentions(self, message: discord.Message) -> bool:
        """فحص الإشارات المشبوهة"""
        # إشارات كثيرة
        if len(message.mentions) > 5:
            return True
        
        # إشارة @everyone أو @here بدون صلاحيات
        if (message.mention_everyone and 
            not message.author.guild_permissions.mention_everyone):
            return True
        
        return False
    
    # معالجات إضافية
    async def _handle_suspicious_content(self, message: discord.Message, pattern: str):
        """معالجة المحتوى المشبوه"""
        await db_manager.add_danger_points(message.guild.id, message.author.id, 2)
        
        await db_manager.add_threat(
            message.guild.id,
            message.author.id,
            "suspicious_content",
            f"Pattern: {pattern}",
            "medium"
        )
    
    async def _handle_dangerous_file(self, message: discord.Message, attachment: discord.Attachment):
        """معالجة الملف الخطير"""
        try:
            await message.delete()
            
            embed = discord.Embed(
                title="🚨 ملف خطير محجوب",
                description=f"تم حجب ملف خطير من {message.author.mention}",
                color=Config.COLORS['error']
            )
            embed.add_field(name="اسم الملف", value=attachment.filename, inline=False)
            
            await message.channel.send(embed=embed, delete_after=10)
            
            await db_manager.add_danger_points(message.guild.id, message.author.id, 4)
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الملف الخطير: {e}")
    
    async def _check_new_account(self, member: discord.Member):
        """فحص الحساب الجديد"""
        account_age = datetime.now() - member.created_at
        
        # حساب جديد (أقل من 7 أيام)
        if account_age.days < 7:
            log_security_event(
                "NEW_ACCOUNT_JOIN",
                member.id,
                member.guild.id,
                f"Account age: {account_age.days} days"
            )
    
    async def _send_security_welcome(self, member: discord.Member):
        """إرسال رسالة ترحيب أمنية"""
        try:
            embed = discord.Embed(
                title="🔒 مرحباً بك في السيرفر الآمن",
                description="يرجى قراءة القوانين والالتزام بالسلوك الآمن",
                color=Config.COLORS['info']
            )
            embed.add_field(
                name="💡 نصائح أمنية",
                value="• لا تضغط على روابط مشبوهة\n• لا تشارك معلوماتك الشخصية\n• بلغ عن أي نشاط مشبوه",
                inline=False
            )
            
            await member.send(embed=embed)
            
        except discord.Forbidden:
            # لا يمكن إرسال رسالة خاصة
            pass
    
    async def _handle_suspicious_name(self, member: discord.Member):
        """معالجة الاسم المشبوه"""
        log_security_event(
            "SUSPICIOUS_NAME",
            member.id,
            member.guild.id,
            f"Name: {member.display_name}"
        )
        
        # يمكن إضافة إجراءات إضافية هنا حسب مستوى الحماية
    
    async def _log_suspicious_edit(self, before: discord.Message, after: discord.Message):
        """تسجيل التعديل المشبوه"""
        log_security_event(
            "SUSPICIOUS_EDIT",
            after.author.id,
            after.guild.id,
            f"Before: {before.content[:50]}... | After: {after.content[:50]}..."
        )
    
    async def _handle_potential_raid(self, guild: discord.Guild, join_count: int):
        """معالجة الهجوم المحتمل"""
        log_security_event(
            "POTENTIAL_RAID",
            0,  # لا يوجد مستخدم محدد
            guild.id,
            f"Rapid joins detected: {join_count} in {Config.RAID_DETECTION_WINDOW}s"
        )
        
        # إرسال تنبيه للإدارة
        embed = discord.Embed(
            title="🚨 تحذير من هجوم محتمل",
            description=f"تم اكتشاف {join_count} انضمام سريع في آخر {Config.RAID_DETECTION_WINDOW} ثانية",
            color=Config.COLORS['error']
        )
        
        await self.bot.send_security_alert(guild.id, embed)