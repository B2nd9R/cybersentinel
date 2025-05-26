import discord
from discord.ext import commands
import json
import random
from datetime import datetime

from config import Config
from core.logger import get_security_logger

logger = get_security_logger()

class SecurityTips:
    """نظام النصائح الأمنية التفاعلية"""
    
    def __init__(self):
        self.tips = []
        self.last_tip = {}
        
    async def initialize(self):
        """تهيئة نظام النصائح الأمنية"""
        try:
            await self._load_tips()
            logger.info("✅ تم تهيئة نظام النصائح الأمنية")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة نظام النصائح: {e}")
    
    async def _load_tips(self):
        """تحميل النصائح من ملف JSON"""
        try:
            with open('data/security_tips.json', 'r', encoding='utf-8') as f:
                self.tips = json.load(f)
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل النصائح: {e}")
            self.tips = []
    
    async def get_random_tip(self, guild_id: int) -> discord.Embed:
        """الحصول على نصيحة أمنية عشوائية"""
        if not self.tips:
            return discord.Embed(
                title="❌ خطأ",
                description="لا توجد نصائح متاحة حالياً",
                color=Config.COLORS['error']
            )
        
        # تجنب تكرار نفس النصيحة
        last_tip = self.last_tip.get(guild_id)
        available_tips = [tip for tip in self.tips if tip != last_tip]
        
        if not available_tips:
            available_tips = self.tips
        
        tip = random.choice(available_tips)
        self.last_tip[guild_id] = tip
        
        return discord.Embed(
            title=f"🔒 {tip['title']}",
            description=tip['content'],
            color=Config.COLORS['info']
        ).add_field(
            name="🏷️ التصنيف",
            value=tip['category'],
            inline=True
        ).add_field(
            name="📈 مستوى الأهمية",
            value=tip['importance'],
            inline=True
        ).set_footer(
            text=f"💡 نصيحة أمنية | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    async def add_tip(self, tip_data: dict) -> bool:
        """إضافة نصيحة أمنية جديدة"""
        try:
            self.tips.append(tip_data)
            await self._save_tips()
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة النصيحة: {e}")
            return False
    
    async def _save_tips(self):
        """حفظ النصائح إلى ملف JSON"""
        try:
            with open('data/security_tips.json', 'w', encoding='utf-8') as f:
                json.dump(self.tips, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ النصائح: {e}")