import discord
from discord.ext import commands
from datetime import datetime
from typing import Optional

from config import Config
from core.logger import get_security_logger

logger = get_security_logger()

class GeneralCommands(commands.Cog):
    """الأوامر العامة للبوت"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='help')
    async def help_command(self, ctx, command: Optional[str] = None):
        """عرض قائمة الأوامر المتاحة"""
        if command:
            # البحث عن الأمر المحدد
            cmd = self.bot.get_command(command)
            if cmd:
                embed = discord.Embed(
                    title=f"📖 معلومات الأمر: {cmd.name}",
                    description=cmd.help or "لا يوجد وصف متاح",
                    color=Config.COLORS.get('info', 0x3498db)
                )
                embed.add_field(name="الاستخدام", value=f"`{ctx.prefix}{cmd.name}`")
                await ctx.send(embed=embed)
                return
            
            await ctx.send(f"❌ الأمر `{command}` غير موجود")
            return
        
        # عرض جميع الأوامر المتاحة
        embed = discord.Embed(
            title="🛡️ قائمة الأوامر المتاحة",
            description=f"استخدم `{ctx.prefix}help <command>` لمزيد من المعلومات عن أمر محدد",
            color=Config.COLORS.get('info', 0x3498db)
        )
        
        for cog_name, cog in self.bot.cogs.items():
            commands_list = [f"`{cmd.name}`" for cmd in cog.get_commands() if not cmd.hidden]
            if commands_list:
                embed.add_field(
                    name=f"{cog_name}",
                    value=" | ".join(commands_list),
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """التحقق من زمن استجابة البوت"""
        start_time = datetime.now()
        message = await ctx.send("🏓 جاري حساب زمن الاستجابة...")
        
        latency = round(self.bot.latency * 1000)
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        embed = discord.Embed(
            title="🏓 بونج!",
            color=Config.COLORS.get('success', 0x2ecc71)
        )
        embed.add_field(name="زمن استجابة الديسكورد", value=f"{latency}ms")
        embed.add_field(name="زمن استجابة البوت", value=f"{round(response_time)}ms")
        
        await message.edit(content=None, embed=embed)
    
    @commands.command(name='info')
    async def show_bot_info(self, ctx):
        """عرض معلومات عن البوت"""
        embed = discord.Embed(
            title="ℹ️ معلومات البوت",
            description="CyberSentinel - بوت الحماية الأمنية لسيرفرات الديسكورد",
            color=Config.COLORS.get('info', 0x3498db)
        )
        
        # إحصائيات عامة
        embed.add_field(name="السيرفرات", value=str(len(self.bot.guilds)))
        embed.add_field(name="المستخدمين", value=str(len(self.bot.users)))
        embed.add_field(name="القنوات", value=str(len(list(self.bot.get_all_channels()))))
        
        # معلومات إضافية
        if hasattr(self.bot, 'start_time'):
            uptime = datetime.now() - self.bot.start_time
            embed.add_field(name="مدة التشغيل", value=str(uptime).split('.')[0])
        
        await ctx.send(embed=embed)