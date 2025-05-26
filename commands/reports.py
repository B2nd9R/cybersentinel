import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import json

from config import Config
from core.logger import get_security_logger, log_security_event
from core.database import db_manager

logger = get_security_logger()

class ReportsCommands(commands.Cog):
    """أوامر التقارير والإحصائيات الأمنية"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='security_report')
    @commands.has_permissions(manage_guild=True)
    async def security_report(self, ctx, days: int = 7):
        """إنشاء تقرير أمني شامل للسيرفر"""
        if days > 30:
            days = 30  # حد أقصى شهر واحد
        
        embed = discord.Embed(
            title="📊 جاري إنشاء التقرير الأمني...",
            description="يرجى الانتظار بينما نجمع البيانات",
            color=Config.COLORS['info']
        )
        message = await ctx.send(embed=embed)
        
        try:
            # جمع البيانات
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # إحصائيات التهديدات
            threats = await db_manager.get_threats_in_period(ctx.guild.id, start_date, end_date)
            threat_types = {}
            for threat in threats:
                threat_type = threat['threat_type']
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
            
            # المستخدمين عالي الخطورة
            high_risk_users = await db_manager.get_high_risk_users(ctx.guild.id)
            
            # الروابط المفحوصة
            scanned_links = await db_manager.get_scanned_links_count(ctx.guild.id, start_date, end_date)
            
            # إنشاء التقرير
            report_embed = discord.Embed(
                title=f"📊 التقرير الأمني - آخر {days} أيام",
                description=f"تقرير شامل للنشاط الأمني في **{ctx.guild.name}**",
                color=Config.COLORS['info'],
                timestamp=datetime.now()
            )
            
            # إحصائيات عامة
            report_embed.add_field(
                name="📈 الإحصائيات العامة",
                value=f"🚨 إجمالي التهديدات: **{len(threats)}**\n"
                      f"👥 مستخدمين عالي الخطورة: **{len(high_risk_users)}**\n"
                      f"🔗 روابط مفحوصة: **{scanned_links}**",
                inline=False
            )
            
            # أنواع التهديدات
            if threat_types:
                threat_list = []
                for threat_type, count in sorted(threat_types.items(), key=lambda x: x[1], reverse=True):
                    threat_list.append(f"• {threat_type}: {count}")
                
                report_embed.add_field(
                    name="🚨 أنواع التهديدات",
                    value="\n".join(threat_list[:10]),  # أول 10 أنواع
                    inline=True
                )
            
            # أكثر المستخدمين خطورة
            if high_risk_users:
                risk_list = []
                for user_data in high_risk_users[:5]:  # أول 5 مستخدمين
                    user = ctx.guild.get_member(user_data['user_id'])
                    if user:
                        risk_list.append(f"• {user.display_name}: {user_data['danger_points']} نقطة")
                
                if risk_list:
                    report_embed.add_field(
                        name="⚠️ أكثر المستخدمين خطورة",
                        value="\n".join(risk_list),
                        inline=True
                    )
            
            # توصيات أمنية
            recommendations = []
            if len(threats) > 50:
                recommendations.append("• نشاط تهديدات عالي - يُنصح بزيادة مستوى الحماية")
            if len(high_risk_users) > 10:
                recommendations.append("• عدد كبير من المستخدمين عالي الخطورة")
            if scanned_links < 10:
                recommendations.append("• قلة فحص الروابط - تأكد من تفعيل الحماية")
            
            if recommendations:
                report_embed.add_field(
                    name="💡 التوصيات",
                    value="\n".join(recommendations),
                    inline=False
                )
            else:
                report_embed.add_field(
                    name="✅ الحالة الأمنية",
                    value="السيرفر في حالة أمنية جيدة",
                    inline=False
                )
            
            await message.edit(embed=report_embed)
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء التقرير: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في التقرير",
                description="حدث خطأ أثناء إنشاء التقرير الأمني",
                color=Config.COLORS['error']
            )
            await message.edit(embed=error_embed)
    
    @commands.command(name='threat_log')
    @commands.has_permissions(manage_messages=True)
    async def threat_log(self, ctx, user: Optional[discord.Member] = None, limit: int = 10):
        """عرض سجل التهديدات"""
        if limit > 50:
            limit = 50
        
        try:
            if user:
                threats = await db_manager.get_user_threats(ctx.guild.id, user.id, limit)
                title = f"📋 سجل التهديدات - {user.display_name}"
            else:
                threats = await db_manager.get_recent_threats(ctx.guild.id, limit)
                title = "📋 سجل التهديدات الأخيرة"
            
            if not threats:
                embed = discord.Embed(
                    title="📋 سجل التهديدات",
                    description="لا توجد تهديدات مسجلة",
                    color=Config.COLORS['info']
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=title,
                color=Config.COLORS['warning'],
                timestamp=datetime.now()
            )
            
            threat_list = []
            for threat in threats:
                user_obj = ctx.guild.get_member(threat['user_id'])
                user_name = user_obj.display_name if user_obj else f"User {threat['user_id']}"
                
                threat_list.append(
                    f"**{threat['threat_type']}** - {user_name}\n"
                    f"📅 {threat['timestamp'][:16]}\n"
                    f"📝 {threat['details'][:100]}{'...' if len(threat['details']) > 100 else ''}\n"
                )
            
            # تقسيم القائمة إلى صفحات
            page_size = 5
            pages = [threat_list[i:i + page_size] for i in range(0, len(threat_list), page_size)]
            
            for i, page in enumerate(pages):
                if i > 0:
                    embed = discord.Embed(
                        title=f"{title} - صفحة {i + 1}",
                        color=Config.COLORS['warning']
                    )
                
                embed.description = "\n".join(page)
                embed.set_footer(text=f"صفحة {i + 1}/{len(pages)}")
                
                await ctx.send(embed=embed)
                
                if i < len(pages) - 1:
                    await asyncio.sleep(1)  # تأخير بسيط بين الصفحات
            
        except Exception as e:
            logger.error(f"خطأ في عرض سجل التهديدات: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في السجل",
                description="حدث خطأ أثناء عرض سجل التهديدات",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=error_embed)
    
    @commands.command(name='export_data')
    @commands.has_permissions(administrator=True)
    async def export_security_data(self, ctx, days: int = 30):
        """تصدير البيانات الأمنية"""
        if days > 90:
            days = 90  # حد أقصى 3 أشهر
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # جمع البيانات
            threats = await db_manager.get_threats_in_period(ctx.guild.id, start_date, end_date)
            scanned_links = await db_manager.get_scanned_links_in_period(ctx.guild.id, start_date, end_date)
            user_scores = await db_manager.get_all_user_scores(ctx.guild.id)
            
            # إنشاء ملف JSON
            export_data = {
                "guild_id": ctx.guild.id,
                "guild_name": ctx.guild.name,
                "export_date": datetime.now().isoformat(),
                "period_days": days,
                "threats": threats,
                "scanned_links": scanned_links,
                "user_danger_scores": user_scores,
                "statistics": {
                    "total_threats": len(threats),
                    "total_scanned_links": len(scanned_links),
                    "high_risk_users": len([u for u in user_scores if u['danger_points'] >= Config.MAX_DANGER_POINTS * 0.8])
                }
            }
            
            # إنشاء ملف مؤقت
            filename = f"security_data_{ctx.guild.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # إرسال الملف
            embed = discord.Embed(
                title="📤 تصدير البيانات الأمنية",
                description=f"تم تصدير البيانات الأمنية لآخر {days} يوم",
                color=Config.COLORS['success']
            )
            
            await ctx.send(embed=embed, file=discord.File(filename))
            
            # حذف الملف المؤقت
            import os
            os.remove(filename)
            
        except Exception as e:
            logger.error(f"خطأ في تصدير البيانات: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في التصدير",
                description="حدث خطأ أثناء تصدير البيانات الأمنية",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=error_embed)
    
    @commands.command(name='stats')
    async def security_stats(self, ctx):
        """عرض إحصائيات أمنية سريعة"""
        try:
            # إحصائيات اليوم
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            today_threats = await db_manager.get_threats_in_period(ctx.guild.id, today, datetime.now())
            total_threats = await db_manager.get_total_threats_count(ctx.guild.id)
            high_risk_users = await db_manager.get_high_risk_users(ctx.guild.id)
            
            embed = discord.Embed(
                title="📊 الإحصائيات الأمنية السريعة",
                color=Config.COLORS['info'],
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📅 اليوم",
                value=f"🚨 تهديدات: {len(today_threats)}",
                inline=True
            )
            
            embed.add_field(
                name="📈 الإجمالي",
                value=f"🚨 تهديدات: {total_threats}\n👥 مستخدمين خطرين: {len(high_risk_users)}",
                inline=True
            )
            
            # حالة الحماية
            protection_level = await db_manager.get_guild_protection_level(ctx.guild.id)
            level_colors = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'maximum': '🔴'
            }
            
            embed.add_field(
                name="🛡️ مستوى الحماية",
                value=f"{level_colors.get(protection_level, '🟢')} {protection_level or 'medium'}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"خطأ في عرض الإحصائيات: {e}")
            error_embed = discord.Embed(
                title="❌ خطأ في الإحصائيات",
                description="حدث خطأ أثناء عرض الإحصائيات",
                color=Config.COLORS['error']
            )
            await ctx.send(embed=error_embed)

def setup(bot):
    bot.add_cog(ReportsCommands(bot))