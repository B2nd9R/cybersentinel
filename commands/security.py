import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from config import Config
from core.logger import get_security_logger, log_security_event
from core.database import db_manager

logger = get_security_logger()

class SecurityCommands(commands.Cog):
    """أوامر الأمان والحماية"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='scan_url')
    async def scan_url(self, ctx, url: str):
        """فحص رابط للتأكد من أمانه"""
        # إرسال رسالة انتظار
        loading_embed = discord.Embed(
            title="🔍 جاري فحص الرابط...",
            description="يرجى الانتظار بينما نقوم بفحص الرابط",
            color=Config.COLORS['info']
        )
        message = await ctx.send(embed=loading_embed)
        
        try:
            # فحص الرابط باستخدام نظام حماية الروابط
            if self.bot.link_guardian:
                scan_result = await self.bot.link_guardian.scan_url(url)
                
                # إنشاء embed النتيجة
                if scan_result.get('is_safe', True):
                    embed = discord.Embed(
                        title="✅ الرابط آمن",
                        description=f"تم فحص الرابط ولم يتم اكتشاف أي تهديدات",
                        color=Config.COLORS['success']
                    )
                else:
                    embed = discord.Embed(
                        title="⚠️ رابط مشبوه",
                        description="تم اكتشاف تهديدات محتملة في هذا الرابط",
                        color=Config.COLORS['error']
                    )
                    
                    threats = scan_result.get('threats_detected', [])
                    if threats:
                        embed.add_field(
                            name="🚨 التهديدات المكتشفة",
                            value="\n".join(threats[:5]),  # أول 5 تهديدات
                            inline=False
                        )
                
                embed.add_field(
                    name="🔗 الرابط",
                    value=f"```{url[:100]}{'...' if len(url) > 100 else ''}```",
                    inline=False
                )
                
                embed.add_field(
                    name="📊 مستوى الثقة",
                    value=f"{scan_result.get('confidence', 0):.1%}",
                    inline=True
                )
                
                embed.add_field(
                    name="🕐 وقت الفحص",
                    value=datetime.now().strftime("%H:%M:%S"),
                    inline=True
                )
                
            else:
                embed = discord.Embed(
                    title="❌ خطأ في الفحص",
                    description="نظام فحص الروابط غير متاح حالياً",
                    color=Config.COLORS['error']
                )
            
            await message.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"خطأ في فحص الرابط: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في الفحص",
                description="حدث خطأ أثناء فحص الرابط",
                color=Config.COLORS['error']
            )
            await message.edit(embed=error_embed)
    
    @commands.command(name='user_info')
    async def user_security_info(self, ctx, user: Optional[discord.Member] = None):
        """عرض معلومات الأمان لمستخدم"""
        if user is None:
            user = ctx.author
        
        # الحصول على بيانات المستخدم
        user_data = await db_manager.get_user_danger_score(ctx.guild.id, user.id)
        
        embed = discord.Embed(
            title=f"🔒 معلومات الأمان - {user.display_name}",
            color=Config.COLORS['info'],
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # نقاط الخطر
        danger_points = user_data.get('danger_points', 0)
        max_points = Config.MAX_DANGER_POINTS
        
        danger_color = "🟢"
        if danger_points >= max_points * 0.8:
            danger_color = "🔴"
        elif danger_points >= max_points * 0.5:
            danger_color = "🟡"
        
        embed.add_field(
            name="⚠️ نقاط الخطر",
            value=f"{danger_color} {danger_points}/{max_points}",
            inline=True
        )
        
        embed.add_field(
            name="📊 إجمالي التحذيرات",
            value=user_data.get('total_warnings', 0),
            inline=True
        )
        
        # آخر مخالفة
        last_violation = user_data.get('last_violation')
        if last_violation:
            embed.add_field(
                name="🕐 آخر مخالفة",
                value=last_violation[:16],
                inline=True
            )
        
        # حالة الحساب
        account_age = datetime.now() - user.created_at
        if account_age.days < 7:
            embed.add_field(
                name="🆕 عمر الحساب",
                value=f"⚠️ حساب جديد ({account_age.days} أيام)",
                inline=False
            )
        
        # التهديدات الأخيرة
        recent_threats = await db_manager.get_user_recent_threats(ctx.guild.id, user.id, 5)
        if recent_threats:
            threat_list = []
            for threat in recent_threats:
                threat_list.append(f"• {threat['threat_type']} ({threat['timestamp'][:10]})")
            
            embed.add_field(
                name="🚨 التهديدات الأخيرة",
                value="\n".join(threat_list),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='warn_user')
    @commands.has_permissions(manage_messages=True)
    async def warn_user(self, ctx, user: discord.Member, *, reason: str):
        """تحذير مستخدم وإضافة نقاط خطر"""
        # إضافة نقاط خطر
        await db_manager.add_danger_points(ctx.guild.id, user.id, 2)
        
        # تسجيل التهديد
        await db_manager.add_threat(
            ctx.guild.id,
            user.id,
            "manual_warning",
            reason,
            "medium"
        )
        
        # إرسال رسالة للمستخدم
        try:
            user_embed = discord.Embed(
                title="⚠️ تحذير أمني",
                description=f"تم تحذيرك في سيرفر **{ctx.guild.name}**",
                color=Config.COLORS['warning']
            )
            user_embed.add_field(name="السبب", value=reason, inline=False)
            user_embed.add_field(
                name="ملاحظة",
                value="يرجى الالتزام بقوانين السيرفر لتجنب المزيد من العقوبات",
                inline=False
            )
            await user.send(embed=user_embed)
        except:
            pass  # في حالة عدم إمكانية إرسال رسالة خاصة
        
        # رسالة تأكيد
        embed = discord.Embed(
            title="✅ تم التحذير",
            description=f"تم تحذير {user.mention} بنجاح",
            color=Config.COLORS['success']
        )
        embed.add_field(name="السبب", value=reason, inline=False)
        
        await ctx.send(embed=embed)
        
        log_security_event(
            "MANUAL_WARNING",
            ctx.author.id,
            ctx.guild.id,
            f"Warned user {user.id}: {reason}"
        )
    
    @commands.command(name='security_scan')
    @commands.has_permissions(manage_guild=True)
    async def security_scan(self, ctx):
        """إجراء فحص أمني شامل للسيرفر"""
        embed = discord.Embed(
            title="🔍 بدء الفحص الأمني الشامل",
            description="جاري فحص السيرفر للتهديدات المحتملة...",
            color=Config.COLORS['info']
        )
        message = await ctx.send(embed=embed)
        
        scan_results = {
            'suspicious_users': 0,
            'high_risk_users': 0,
            'recent_threats': 0,
            'recommendations': []
        }
        
        try:
            # فحص المستخدمين عالي الخطورة
            high_risk_users = await db_manager.get_high_risk_users(ctx.guild.id)
            scan_results['high_risk_users'] = len(high_risk_users)
            
            # فحص التهديدات الأخيرة
            recent_threats = await db_manager.get_recent_threats(ctx.guild.id, 24)  # آخر 24 ساعة
            scan_results['recent_threats'] = len(recent_threats)
            
            # فحص الأعضاء الجدد المشبوهين
            suspicious_count = 0
            for member in ctx.guild.members:
                if not member.bot:
                    account_age = datetime.now() - member.created_at
                    if account_age.days < 1:  # حسابات أقل من يوم
                        suspicious_count += 1
            
            scan_results['suspicious_users'] = suspicious_count
            
            # توصيات
            if scan_results['high_risk_users'] > 5:
                scan_results['recommendations'].append("يوجد عدد كبير من المستخدمين عالي الخطورة")
            
            if scan_results['recent_threats'] > 10:
                scan_results['recommendations'].append("نشاط تهديدات عالي - يُنصح بزيادة مستوى الحماية")
            
            if scan_results['suspicious_users'] > 10:
                scan_results['recommendations'].append("عدد كبير من الحسابات الجديدة - احذر من الهجمات")
            
            # إنشاء embed النتائج
            result_embed = discord.Embed(
                title="📊 نتائج الفحص الأمني",
                description="تم إكمال الفحص الأمني الشامل",
                color=Config.COLORS['success'] if not scan_results['recommendations'] else Config.COLORS['warning']
            )
            
            result_embed.add_field(
                name="👥 مستخدمين عالي الخطورة",
                value=scan_results['high_risk_users'],
                inline=True
            )
            
            result_embed.add_field(
                name="🚨 تهديدات حديثة",
                value=scan_results['recent_threats'],
                inline=True
            )
            
            result_embed.add_field(
                name="🆕 حسابات مشبوهة",
                value=scan_results['suspicious_users'],
                inline=True
            )
            
            if scan_results['recommendations']:
                result_embed.add_field(
                    name="💡 التوصيات",
                    value="\n".join(f"• {rec}" for rec in scan_results['recommendations']),
                    inline=False
                )
            else:
                result_embed.add_field(
                    name="✅ الحالة",
                    value="السيرفر آمن ولا توجد تهديدات كبيرة",
                    inline=False
                )
            
            await message.edit(embed=result_embed)
            
        except Exception as e:
            logger.error(f"خطأ في الفحص الأمني: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في الفحص",
                description="حدث خطأ أثناء إجراء الفحص الأمني",
                color=Config.COLORS['error']
            )
            await message.edit(embed=error_embed)
    
    @commands.command(name='lockdown')
    @commands.has_permissions(administrator=True)
    async def server_lockdown(self, ctx, duration: int = 10):
        """قفل السيرفر مؤقتاً (بالدقائق)"""
        if duration > 60:
            duration = 60  # حد أقصى ساعة واحدة
        
        # حفظ الصلاحيات الأصلية
        original_permissions = {}
        
        try:
            # إزالة صلاحية الإرسال من جميع القنوات
            for channel in ctx.guild.text_channels:
                if channel.permissions_for(ctx.guild.default_role).send_messages:
                    original_permissions[channel.id] = True
                    await channel.set_permissions(
                        ctx.guild.default_role,
                        send_messages=False,
                        reason=f"Server lockdown by {ctx.author}"
                    )
            
            embed = discord.Embed(
                title="🔒 تم قفل السيرفر",
                description=f"تم قفل السيرفر لمدة {duration} دقيقة لأسباب أمنية",
                color=Config.COLORS['error']
            )
            embed.add_field(
                name="⏰ مدة القفل",
                value=f"{duration} دقيقة",
                inline=True
            )
            embed.add_field(
                name="👮 بواسطة",
                value=ctx.author.mention,
                inline=True
            )
            
            await ctx.send(embed=embed)
            
            # انتظار المدة المحددة
            await asyncio.sleep(duration * 60)
            
            # إعادة الصلاحيات
            for channel_id in original_permissions:
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    await channel.set_permissions(
                        ctx.guild.default_role,
                        send_messages=None,
                        reason="Lockdown ended"
                    )
            
            unlock_embed = discord.Embed(
                title="🔓 تم إلغاء قفل السيرفر",
                description="انتهت مدة القفل وتم إعادة السيرفر للوضع الطبيعي",
                color=Config.COLORS['success']
            )
            
            await ctx.send(embed=unlock_embed)
            
            log_security_event(
                "SERVER_UNLOCK",
                ctx.author.id,
                ctx.guild.id,
                f"Server lockdown ended after {duration} minutes"
            )
            
        except Exception as e:
            logger.error(f"خطأ في قفل السيرفر: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في القفل",
                description="حدث خطأ أثناء قفل السيرفر",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=error_embed)
    
    @commands.command(name='clear_threats')
    @commands.has_permissions(administrator=True)
    async def clear_threats(self, ctx, user: Optional[discord.Member] = None):
        """مسح سجل التهديدات لمستخدم أو للسيرفر بالكامل"""
        if user:
            # مسح تهديدات مستخدم محدد
            await db_manager.clear_user_threats(ctx.guild.id, user.id)
            embed = discord.Embed(
                title="✅ تم مسح التهديدات",
                description=f"تم مسح جميع تهديدات {user.mention}",
                color=Config.COLORS['success']
            )
        else:
            # مسح جميع التهديدات في السيرفر
            await db_manager.clear_all_threats(ctx.guild.id)
            embed = discord.Embed(
                title="✅ تم مسح جميع التهديدات",
                description="تم مسح جميع سجلات التهديدات في السيرفر",
                color=Config.COLORS['success']
            )
        
        await ctx.send(embed=embed)
        
        log_security_event(
            "THREATS_CLEARED",
            ctx.author.id,
            ctx.guild.id,
            f"Cleared threats for {'user ' + str(user.id) if user else 'entire server'}"
        )
    
    @commands.command(name='protection_level')
    @commands.has_permissions(manage_guild=True)
    async def set_protection_level(self, ctx, level: str):
        """تعيين مستوى الحماية للسيرفر"""
        valid_levels = ['low', 'medium', 'high', 'maximum']
        level = level.lower()
        
        if level not in valid_levels:
            embed = discord.Embed(
                title="❌ مستوى حماية غير صحيح",
                description=f"المستويات المتاحة: {', '.join(valid_levels)}",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=embed)
            return
        
        # حفظ مستوى الحماية في قاعدة البيانات
        await db_manager.set_guild_protection_level(ctx.guild.id, level)
        
        level_descriptions = {
            'low': '🟢 منخفض - حماية أساسية',
            'medium': '🟡 متوسط - حماية متوازنة',
            'high': '🟠 عالي - حماية مشددة',
            'maximum': '🔴 أقصى - حماية قصوى'
        }
        
        embed = discord.Embed(
            title="🛡️ تم تحديث مستوى الحماية",
            description=f"مستوى الحماية الجديد: {level_descriptions[level]}",
            color=Config.COLORS['success']
        )
        
        await ctx.send(embed=embed)
        
        log_security_event(
            "PROTECTION_LEVEL_CHANGED",
            ctx.author.id,
            ctx.guild.id,
            f"Protection level changed to {level}"
        )
    
    @commands.command(name='quarantine')
    @commands.has_permissions(manage_roles=True)
    async def quarantine_user(self, ctx, user: discord.Member, duration: int = 60):
        """عزل مستخدم مؤقتاً (بالدقائق)"""
        if duration > 1440:  # حد أقصى 24 ساعة
            duration = 1440
        
        try:
            # إنشاء أو الحصول على رول العزل
            quarantine_role = discord.utils.get(ctx.guild.roles, name="Quarantined")
            if not quarantine_role:
                quarantine_role = await ctx.guild.create_role(
                    name="Quarantined",
                    color=discord.Color.dark_red(),
                    reason="Security quarantine role"
                )
                
                # إزالة جميع الصلاحيات من رول العزل
                for channel in ctx.guild.channels:
                    await channel.set_permissions(
                        quarantine_role,
                        send_messages=False,
                        add_reactions=False,
                        speak=False,
                        connect=False
                    )
            
            # حفظ الأدوار الأصلية
            original_roles = [role for role in user.roles if role != ctx.guild.default_role]
            
            # إزالة جميع الأدوار وإضافة رول العزل
            await user.edit(roles=[quarantine_role], reason=f"Quarantined by {ctx.author}")
            
            embed = discord.Embed(
                title="🔒 تم عزل المستخدم",
                description=f"تم عزل {user.mention} لمدة {duration} دقيقة",
                color=Config.COLORS['warning']
            )
            
            await ctx.send(embed=embed)
            
            # إرسال رسالة للمستخدم
            try:
                user_embed = discord.Embed(
                    title="🔒 تم عزلك مؤقتاً",
                    description=f"تم عزلك في سيرفر **{ctx.guild.name}** لمدة {duration} دقيقة",
                    color=Config.COLORS['warning']
                )
                await user.send(embed=user_embed)
            except:
                pass
            
            # انتظار انتهاء مدة العزل
            await asyncio.sleep(duration * 60)
            
            # إعادة الأدوار الأصلية
            await user.edit(roles=original_roles, reason="Quarantine period ended")
            
            release_embed = discord.Embed(
                title="🔓 انتهى العزل",
                description=f"انتهت مدة عزل {user.mention}",
                color=Config.COLORS['success']
            )
            
            await ctx.send(embed=release_embed)
            
            log_security_event(
                "USER_QUARANTINE",
                ctx.author.id,
                ctx.guild.id,
                f"User {user.id} quarantined for {duration} minutes"
            )
            
        except Exception as e:
            logger.error(f"خطأ في عزل المستخدم: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في العزل",
                description="حدث خطأ أثناء عزل المستخدم",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=error_embed)

def setup(bot):
    bot.add_cog(SecurityCommands(bot))