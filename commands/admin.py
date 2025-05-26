import discord
from discord.ext import commands
from typing import Optional
from datetime import datetime

from config import Config
from core.logger import get_security_logger, log_security_event
from core.database import db_manager

logger = get_security_logger()

class AdminCommands(commands.Cog):
    """أوامر الإدارة والتحكم في البوت"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """التحقق من صلاحيات الإدارة"""
        if not ctx.guild:
            return False
        
        # التحقق من صلاحيات الإدارة
        return (
            ctx.author.guild_permissions.administrator or
            ctx.author.id == Config.OWNER_ID or
            any(role.name == Config.ADMIN_ROLE_NAME for role in ctx.author.roles)
        )
    
    @commands.command(name='setup')
    async def setup_bot(self, ctx):
        """إعداد البوت في السيرفر"""
        embed = discord.Embed(
            title="🔧 إعداد بوت الحماية الأمنية",
            description="مرحباً بك في إعداد البوت! سأقوم بإرشادك خلال العملية.",
            color=Config.COLORS['info']
        )
        
        # إنشاء إعدادات افتراضية
        await db_manager.create_default_guild_settings(ctx.guild.id)
        
        embed.add_field(
            name="✅ تم الإعداد الأساسي",
            value="تم إنشاء إعدادات افتراضية للسيرفر",
            inline=False
        )
        
        embed.add_field(
            name="📋 الخطوات التالية",
            value=(
                "• `!set_admin_channel #channel` - تحديد قناة الإدارة\n"
                "• `!protection_level 2` - تحديد مستوى الحماية (1-4)\n"
                "• `!security_status` - عرض حالة الأمان\n"
                "• `!help` - عرض جميع الأوامر"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        log_security_event(
            "BOT_SETUP",
            ctx.author.id,
            ctx.guild.id,
            f"Bot setup completed by {ctx.author}"
        )
    
    @commands.command(name='set_admin_channel')
    async def set_admin_channel(self, ctx, channel: discord.TextChannel):
        """تحديد قناة الإدارة"""
        await db_manager.update_guild_settings(
            ctx.guild.id,
            admin_channel_id=channel.id
        )
        
        embed = discord.Embed(
            title="✅ تم تحديد قناة الإدارة",
            description=f"تم تعيين {channel.mention} كقناة إدارة",
            color=Config.COLORS['success']
        )
        
        await ctx.send(embed=embed)
        
        # إرسال رسالة تأكيد في القناة المحددة
        test_embed = discord.Embed(
            title="🔒 قناة الإدارة الأمنية",
            description="تم تعيين هذه القناة لاستقبال التنبيهات الأمنية",
            color=Config.COLORS['info']
        )
        await channel.send(embed=test_embed)
    
    @commands.command(name='protection_level')
    async def set_protection_level(self, ctx, level: int):
        """تحديد مستوى الحماية (1-4)"""
        if level not in range(1, 5):
            embed = discord.Embed(
                title="❌ مستوى حماية غير صحيح",
                description="يجب أن يكون مستوى الحماية بين 1 و 4",
                color=Config.COLORS['error']
            )
            embed.add_field(
                name="مستويات الحماية",
                value=(
                    "**1** - أساسي: فحص أساسي فقط\n"
                    "**2** - قياسي: فحص شامل + تحذيرات\n"
                    "**3** - متقدم: فحص شامل + إجراءات تلقائية\n"
                    "**4** - أقصى: حماية قصوى + حظر فوري"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        await db_manager.update_guild_settings(
            ctx.guild.id,
            protection_level=level
        )
        
        level_name = Config.PROTECTION_LEVELS[level]
        embed = discord.Embed(
            title="🛡️ تم تحديث مستوى الحماية",
            description=f"تم تعيين مستوى الحماية إلى: **{level} - {level_name}**",
            color=Config.COLORS['success']
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ban_threshold')
    async def set_ban_threshold(self, ctx, threshold: int):
        """تحديد عتبة الحظر التلقائي"""
        if threshold < 1 or threshold > 50:
            embed = discord.Embed(
                title="❌ عتبة غير صحيحة",
                description="يجب أن تكون عتبة الحظر بين 1 و 50",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=embed)
            return
        
        await db_manager.update_guild_settings(
            ctx.guild.id,
            auto_ban_threshold=threshold
        )
        
        embed = discord.Embed(
            title="⚖️ تم تحديث عتبة الحظر",
            description=f"سيتم حظر المستخدمين تلقائياً عند وصولهم لـ **{threshold}** نقطة خطر",
            color=Config.COLORS['success']
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='toggle_feature')
    async def toggle_feature(self, ctx, feature: str):
        """تفعيل/إلغاء تفعيل ميزة معينة"""
        valid_features = {
            'link_scan': 'link_scan_enabled',
            'anti_raid': 'anti_raid_enabled',
            'behavior_monitoring': 'behavior_monitoring'
        }
        
        if feature not in valid_features:
            embed = discord.Embed(
                title="❌ ميزة غير صحيحة",
                description=f"الميزات المتاحة: {', '.join(valid_features.keys())}",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=embed)
            return
        
        # الحصول على الحالة الحالية
        settings = await db_manager.get_guild_settings(ctx.guild.id)
        current_state = settings.get(valid_features[feature], True)
        new_state = not current_state
        
        # تحديث الإعدادات
        await db_manager.update_guild_settings(
            ctx.guild.id,
            **{valid_features[feature]: new_state}
        )
        
        status = "مفعلة" if new_state else "معطلة"
        embed = discord.Embed(
            title=f"🔄 تم تحديث الميزة",
            description=f"ميزة **{feature}** الآن {status}",
            color=Config.COLORS['success'] if new_state else Config.COLORS['warning']
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='security_status')
    async def security_status(self, ctx):
        """عرض حالة الأمان الحالية"""
        settings = await db_manager.get_guild_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title="🔒 حالة الأمان",
            description=f"حالة الحماية الأمنية لسيرفر **{ctx.guild.name}**",
            color=Config.COLORS['info'],
            timestamp=datetime.now()
        )
        
        # معلومات أساسية
        protection_level = settings.get('protection_level', 2)
        embed.add_field(
            name="🛡️ مستوى الحماية",
            value=f"{protection_level} - {Config.PROTECTION_LEVELS[protection_level]}",
            inline=True
        )
        
        embed.add_field(
            name="⚖️ عتبة الحظر التلقائي",
            value=f"{settings.get('auto_ban_threshold', 10)} نقطة",
            inline=True
        )
        
        # قناة الإدارة
        admin_channel_id = settings.get('admin_channel_id')
        admin_channel = ctx.guild.get_channel(admin_channel_id) if admin_channel_id else None
        embed.add_field(
            name="📢 قناة الإدارة",
            value=admin_channel.mention if admin_channel else "غير محددة",
            inline=True
        )
        
        # الميزات
        features_status = []
        features = {
            'فحص الروابط': settings.get('link_scan_enabled', True),
            'مكافحة الهجمات': settings.get('anti_raid_enabled', True),
            'مراقبة السلوك': settings.get('behavior_monitoring', True)
        }
        
        for feature, enabled in features.items():
            status = "✅" if enabled else "❌"
            features_status.append(f"{status} {feature}")
        
        embed.add_field(
            name="🔧 الميزات",
            value="\n".join(features_status),
            inline=False
        )
        
        # إحصائيات
        stats = await db_manager.get_guild_security_stats(ctx.guild.id)
        if stats:
            embed.add_field(
                name="📊 إحصائيات اليوم",
                value=(
                    f"🚫 تهديدات محجوبة: {stats.get('threats_detected', 0)}\n"
                    f"🔗 روابط مفحوصة: {stats.get('links_scanned', 0)}\n"
                    f"⚠️ مستخدمين محذرين: {stats.get('users_warned', 0)}"
                ),
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='reset_user')
    async def reset_user_danger(self, ctx, user: discord.Member):
        """إعادة تعيين نقاط الخطر لمستخدم"""
        await db_manager.reset_user_danger_points(ctx.guild.id, user.id)
        
        embed = discord.Embed(
            title="🔄 تم إعادة التعيين",
            description=f"تم إعادة تعيين نقاط الخطر للمستخدم {user.mention}",
            color=Config.COLORS['success']
        )
        
        await ctx.send(embed=embed)
        
        log_security_event(
            "USER_RESET",
            ctx.author.id,
            ctx.guild.id,
            f"Reset danger points for user {user.id}"
        )
    
    @commands.command(name='view_threats')
    async def view_recent_threats(self, ctx, limit: int = 10):
        """عرض التهديدات الأخيرة"""
        if limit > 50:
            limit = 50
        
        threats = await db_manager.get_recent_threats(ctx.guild.id, limit)
        
        if not threats:
            embed = discord.Embed(
                title="✅ لا توجد تهديدات",
                description="لم يتم اكتشاف أي تهديدات مؤخراً",
                color=Config.COLORS['success']
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="⚠️ التهديدات الأخيرة",
            description=f"آخر {len(threats)} تهديد تم اكتشافه",
            color=Config.COLORS['warning']
        )
        
        for threat in threats[:10]:  # عرض أول 10 فقط
            user = ctx.guild.get_member(threat['user_id'])
            user_name = user.display_name if user else f"مستخدم {threat['user_id']}"
            
            embed.add_field(
                name=f"🚨 {threat['threat_type']}",
                value=(
                    f"**المستخدم:** {user_name}\n"
                    f"**الخطورة:** {threat['severity']}\n"
                    f"**التاريخ:** {threat['timestamp'][:16]}"
                ),
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='export_data')
    async def export_security_data(self, ctx):
        """تصدير بيانات الأمان"""
        # هذا الأمر يتطلب تطوير إضافي لتصدير البيانات
        embed = discord.Embed(
            title="📤 تصدير البيانات",
            description="هذه الميزة قيد التطوير وستكون متاحة قريباً",
            color=Config.COLORS['info']
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))