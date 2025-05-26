# استيراد المكتبات
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
from typing import Optional

# استيراد الاعدادات
from config import Config
from core.logger import setup_logger, get_security_logger
from core.database import db_manager

# استيراد معالج الأحداث (إذا كان موجوداً)
try:
    from bot.events import EventHandler
except ImportError:
    EventHandler = None

# استيراد الأنظمة الأمنية (مع معالجة الأخطاء)
try:
    from security.link_guardian import LinkGuardian
except ImportError:
    LinkGuardian = None

try:
    from security.behavior_watchdog import BehaviorWatchdog
except ImportError:
    BehaviorWatchdog = None

try:
    from security.anti_raid import AntiRaidSystem
except ImportError:
    AntiRaidSystem = None

try:
    from security.threat_analyzer import ThreatAnalyzer
except ImportError:
    ThreatAnalyzer = None

# استيراد الأوامر (مع معالجة الأخطاء)
try:
    from commands.admin import AdminCommands
except ImportError:
    AdminCommands = None

try:
    from commands.security import SecurityCommands
except ImportError:
    SecurityCommands = None

try:
    from commands.reports import ReportsCommands
except ImportError:
    ReportsCommands = None

try:
    from commands.general import GeneralCommands
except ImportError:
    GeneralCommands = None

# استيراد الأكاديمية (مع معالجة الأخطاء)
try:
    from academy.security_tips import SecurityAcademy
except ImportError:
    SecurityAcademy = None

# إعداد اللوجر
logger = setup_logger()
security_logger = get_security_logger()

class SecurityBot(commands.Bot):
    """البوت الرئيسي للحماية الأمنية"""
    
    def __init__(self, command_prefix=None, intents=None, config=None, db_manager=None):
        # إعداد الـ Intents
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            intents.guilds = True
            intents.guild_messages = True
            intents.dm_messages = True

        # إعداد البادئة
        if command_prefix is None:
            command_prefix = self._get_prefix

        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            description="🔒 بوت الحماية الأمنية لسيرفرات الديسكورد",
            help_command=None,  # سنستخدم help مخصص
            case_insensitive=True
        )
        
        # الحالة والإعدادات
        self.config = config or Config
        self.start_time = datetime.now()
        self.ready = False
        self.db_manager = db_manager  # إضافة db_manager كخاصية للبوت
        
        # الأنظمة الأمنية
        self.link_guardian = None
        self.behavior_watchdog = None
        self.anti_raid = None
        self.threat_analyzer = None
        self.security_academy = None
        
        # معالج الأحداث
        self.event_handler = None
        
        # إحصائيات البوت
        self.stats = {
            'threats_blocked': 0,
            'links_scanned': 0,
            'users_warned': 0,
            'raids_prevented': 0
        }
    
    async def _get_prefix(self, bot, message):
        """الحصول على بادئة الأوامر (يمكن تخصيصها لاحقًا)"""
        if not message.guild:
            return getattr(self.config, 'COMMAND_PREFIX', '!')
        
        # يمكن إضافة منطق للبادئات المخصصة لكل سيرفر
        return getattr(self.config, 'COMMAND_PREFIX', '!')
    
    async def setup_hook(self):
        """إعداد البوت قبل الاتصال"""
        logger.info("🔧 بدء إعداد البوت...")
        
        try:
            # إعداد قاعدة البيانات (إذا كانت متوفرة)
            if hasattr(self, 'db_manager') and db_manager:
                await db_manager.initialize()
            
            # إعداد الأنظمة الأمنية
            await self._setup_security_systems()
            
            # إعداد معالج الأحداث
            if EventHandler:
                self.event_handler = EventHandler(self)
            
            # تحميل الأوامر
            await self._load_commands()
            
            # بدء المهام الخلفية
            self._start_background_tasks()
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد البوت: {e}")
            # لا نرفع الخطأ لتجنب توقف البوت
    
    async def _load_commands(self):
        """تحميل أوامر البوت"""
        try:
            # الأوامر العامة
            if GeneralCommands:
                await self.add_cog(GeneralCommands(self))
            
            # أوامر الإدارة
            async def setup_commands(self):
                """تسجيل جميع الأوامر"""
                try:
                    if AdminCommands:
                        await self.add_cog(AdminCommands(self))
                        logger.info("✅ تم تحميل أوامر الإدارة")
                        
                    if SecurityCommands:
                        await self.add_cog(SecurityCommands(self))
                        logger.info("✅ تم تحميل أوامر الأمان")
                        
                    if ReportsCommands:
                        await self.add_cog(ReportsCommands(self))
                        logger.info("✅ تم تحميل أوامر التقارير")
                        
                    if GeneralCommands:
                        await self.add_cog(GeneralCommands(self))
                        logger.info("✅ تم تحميل الأوامر العامة")
                        
                except Exception as e:
                    logger.error(f"❌ خطأ في تحميل الأوامر: {e}")
            
            logger.info("📝 تم تحميل الأوامر المتوفرة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الأوامر: {e}")
    
    def _start_background_tasks(self):
        """بدء المهام الخلفية"""
        try:
            # مهمة النصائح الأمنية
            if hasattr(self, 'security_tips_task'):
                self.security_tips_task.start()
            
            # مهمة تنظيف قاعدة البيانات
            if hasattr(self, 'cleanup_task'):
                self.cleanup_task.start()
            
            # مهمة تحديث الإحصائيات
            if hasattr(self, 'stats_update_task'):
                self.stats_update_task.start()
            
            logger.info("⚙️ تم بدء المهام الخلفية المتوفرة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد البوت: {e}")
            # لا نرفع الخطأ لتجنب توقف البوت
    
    async def _setup_security_systems(self):
        """إعداد الأنظمة الأمنية"""
        try:
            # نظام حماية الروابط
            if LinkGuardian:
                api_key = getattr(self.config, 'VIRUSTOTAL_API_KEY', None)
                self.link_guardian = LinkGuardian(api_key)
                await self.link_guardian.initialize()
            
            # نظام مراقبة السلوك
            if BehaviorWatchdog:
                self.behavior_watchdog = BehaviorWatchdog()
                await self.behavior_watchdog.initialize()
            
            # نظام مكافحة الهجمات
            if AntiRaidSystem:
                self.anti_raid = AntiRaidSystem()
                await self.anti_raid.initialize()
            
            # محلل التهديدات
            if ThreatAnalyzer:
                self.threat_analyzer = ThreatAnalyzer()
                await self.threat_analyzer.initialize()
            
            # الأكاديمية الأمنية
            if SecurityAcademy:
                self.security_academy = SecurityAcademy()
                await self.security_academy.initialize()
            
            logger.info("🛡️ تم إعداد الأنظمة الأمنية المتوفرة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد الأنظمة الأمنية: {e}")
    
    async def _load_commands(self):
        """تحميل أوامر البوت"""
        try:
            # أوامر الإدارة
            if AdminCommands:
                await self.add_cog(AdminCommands(self))
            
            # أوامر الأمان
            if SecurityCommands:
                await self.add_cog(SecurityCommands(self))
            
            # أوامر البلاغات
            if ReportsCommands:
                await self.add_cog(ReportsCommands(self))
            
            logger.info("📝 تم تحميل الأوامر المتوفرة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الأوامر: {e}")
    
    def _start_background_tasks(self):
        """بدء المهام الخلفية"""
        try:
            # مهمة النصائح الأمنية
            if hasattr(self, 'security_tips_task'):
                self.security_tips_task.start()
            
            # مهمة تنظيف قاعدة البيانات
            if hasattr(self, 'cleanup_task'):
                self.cleanup_task.start()
            
            # مهمة تحديث الإحصائيات
            if hasattr(self, 'stats_update_task'):
                self.stats_update_task.start()
    
            logger.info("⚙️ تم بدء المهام الخلفية المتوفرة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء المهام الخلفية: {e}")
    
    async def on_ready(self):
        """عند اكتمال اتصال البوت"""
        self.ready = True
        
        # إعداد حالة البوت
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"🔒 {len(self.guilds)} سيرفر | !help"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
        
        # طباعة معلومات البوت
        logger.info("=" * 50)
        logger.info(f"🤖 البوت: {self.user}")
        logger.info(f"🆔 المعرف: {self.user.id}")
        logger.info(f"🌐 السيرفرات: {len(self.guilds)}")
        logger.info(f"👥 المستخدمين: {len(self.users)}")
        logger.info(f"🕐 وقت البدء: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)
        logger.info("🔒 بوت الحماية الأمنية جاهز للعمل!")
        
        # إرسال رسالة للمطور
        owner_id = getattr(self.config, 'OWNER_ID', None)
        if owner_id:
            try:
                owner = await self.fetch_user(owner_id)
                embed = discord.Embed(
                    title="🔒 بوت الحماية الأمنية",
                    description="تم تشغيل البوت بنجاح!",
                    color=getattr(self.config, 'COLORS', {}).get('success', 0x00ff00),
                    timestamp=datetime.now()
                )
                embed.add_field(name="السيرفرات", value=len(self.guilds), inline=True)
                embed.add_field(name="المستخدمين", value=len(self.users), inline=True)
                embed.add_field(name="البنج", value=f"{round(self.latency * 1000)}ms", inline=True)
                
                await owner.send(embed=embed)
            except:
                pass  # في حالة عدم إمكانية إرسال رسالة للمطور
    
    async def on_guild_join(self, guild):
        """عند انضمام البوت لسيرفر جديد"""
        logger.info(f"📥 انضم البوت للسيرفر: {guild.name} ({guild.id})")
        
        # إنشاء إعدادات افتراضية للسيرفر (إذا كان db_manager متوفراً)
        if hasattr(self, 'db_manager') and db_manager:
            try:
                await db_manager.create_default_guild_settings(guild.id)
            except:
                pass
        
        # البحث عن قناة الإدارة أو النظام
        admin_channel = None
        for channel in guild.text_channels:
            if any(keyword in channel.name.lower() for keyword in ['admin', 'mod', 'security', 'system']):
                admin_channel = channel
                break
        
        # رسالة ترحيب
        if admin_channel and admin_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="🔒 مرحباً بكم في بوت الحماية الأمنية!",
                description="شكراً لإضافة البوت إلى سيرفركم. سأقوم بحماية سيرفركم من التهديدات الأمنية.",
                color=getattr(self.config, 'COLORS', {}).get('info', 0x0099ff)
            )
            embed.add_field(
                name="📋 البدء السريع",
                value="• `!setup` - إعداد البوت\n• `!help` - عرض المساعدة\n• `!security_status` - حالة الأمان",
                inline=False
            )
            embed.add_field(
                name="🛡️ الميزات الرئيسية",
                value="• فحص الروابط الخبيثة\n• مراقبة السلوك المشبوه\n• حماية من الهجمات\n• نصائح أمنية",
                inline=False
            )
            
            try:
                await admin_channel.send(embed=embed)
            except:
                pass
    
    async def on_guild_remove(self, guild):
        """عند إزالة البوت من سيرفر"""
        logger.info(f"📤 تم إزالة البوت من السيرفر: {guild.name} ({guild.id})")
    
    # المهام الدورية (اختيارية)
    @tasks.loop(hours=24)
    async def security_tips_task(self):
        """مهمة إرسال النصائح الأمنية اليومية"""
        if not self.ready or not self.security_academy:
            return
        
        try:
            await self.security_academy.send_daily_tips()
        except Exception as e:
            logger.error(f"خطأ في إرسال النصائح الأمنية: {e}")
    
    @tasks.loop(hours=6)
    async def cleanup_task(self):
        """مهمة تنظيف قاعدة البيانات"""
        if not self.ready or not hasattr(self, 'db_manager') or not db_manager:
            return
        
        try:
            await db_manager.cleanup_old_data(days=90)
        except Exception as e:
            logger.error(f"خطأ في تنظيف قاعدة البيانات: {e}")
    
    @tasks.loop(minutes=30)
    async def stats_update_task(self):
        """مهمة تحديث إحصائيات البوت"""
        if not self.ready:
            return
        
        try:
            # تحديث حالة البوت
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"🔒 {len(self.guilds)} سيرفر | {self.stats['threats_blocked']} تهديد محجوب"
            )
            await self.change_presence(activity=activity)
        except Exception as e:
            logger.error(f"خطأ في تحديث الإحصائيات: {e}")
    
    # وظائف مساعدة
    async def get_admin_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        """الحصول على قناة الإدارة للسيرفر"""
        if hasattr(self, 'db_manager') and db_manager:
            try:
                settings = await db_manager.get_guild_settings(guild_id)
                
                if settings.get('admin_channel_id'):
                    channel = self.get_channel(settings['admin_channel_id'])
                    if channel:
                        return channel
            except:
                pass
        
        # البحث عن قناة مناسبة
        guild = self.get_guild(guild_id)
        if guild:
            for channel in guild.text_channels:
                if any(keyword in channel.name.lower() for keyword in ['admin', 'mod', 'security', 'log']):
                    return channel
        
        return None
    
    async def send_security_alert(self, guild_id: int, embed: discord.Embed):
        """إرسال تنبيه أمني لقناة الإدارة"""
        admin_channel = await self.get_admin_channel(guild_id)
        
        if admin_channel:
            try:
                await admin_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"لا توجد صلاحية لإرسال رسالة في قناة الإدارة: {guild_id}")
            except Exception as e:
                logger.error(f"خطأ في إرسال التنبيه الأمني: {e}")
    
    async def close(self):
        """إغلاق البوت وتنظيف الموارد"""
        logger.info("🔄 بدء إغلاق البوت...")
        
        # إيقاف المهام الدورية
        if hasattr(self, 'security_tips_task'):
            self.security_tips_task.cancel()
        if hasattr(self, 'cleanup_task'):
            self.cleanup_task.cancel()
        if hasattr(self, 'stats_update_task'):
            self.stats_update_task.cancel()
        
        # إغلاق قاعدة البيانات
        if hasattr(self, 'db_manager') and db_manager:
            try:
                await db_manager.close()
            except:
                pass
        
        # إغلاق البوت
        await super().close()
        logger.info("👋 تم إغلاق البوت بنجاح")