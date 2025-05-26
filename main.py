import asyncio
import logging
import sys
import discord
from discord.ext import commands

from bot.client import SecurityBot
from config import Config

# استيراد قاعدة البيانات مع معالجة الأخطاء
try:
    from core.database import db_manager  # تم تغيير هذا السطر
except ImportError:
    db_manager = None

from core.logger import setup_logging

# --- إعداد التسجيل ---
setup_logging()
logger = logging.getLogger(__name__)

# --- دالة رئيسية لتشغيل البوت ---
async def main():
    """الدالة الرئيسية لتهيئة وتشغيل البوت."""
    logger.info("بدء تشغيل CyberSentinel Bot...")

    # --- التحقق من وجود توكن البوت ---
    token = getattr(Config, 'DISCORD_BOT_TOKEN', None) or getattr(Config, 'DISCORD_TOKEN', None)
    if not token:
        logger.critical("لم يتم العثور على توكن البوت (DISCORD_BOT_TOKEN) في الإعدادات!")
        logger.critical("يرجى التأكد من إعداد ملف .env بشكل صحيح.")
        sys.exit(1)

    # --- تهيئة قاعدة البيانات ---
    if db_manager:
        try:
            await db_manager.initialize()  # تم تعديل هذا السطر
            logger.info("تم الاتصال بقاعدة البيانات بنجاح.")
        except Exception as e:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            logger.warning("سيتم تشغيل البوت بدون قاعدة البيانات.")
    else:
        logger.warning("وحدة قاعدة البيانات غير متوفرة، سيتم تشغيل البوت بدونها.")

    # --- تهيئة نوايا (Intents) البوت ---
    intents = discord.Intents.default()
    intents.message_content = True  # مطلوب لقراءة محتوى الرسائل
    intents.members = True          # مطلوب لتتبع الأعضاء (مثل نظام مكافحة الإغارة)
    intents.guilds = True           # مطلوب لأحداث الخادم

    # --- إنشاء وتشغيل البوت ---
    prefix = getattr(Config, 'BOT_PREFIX', getattr(Config, 'COMMAND_PREFIX', '!'))
    bot = SecurityBot(
        command_prefix=commands.when_mentioned_or(prefix),
        intents=intents,
        config=Config,
        db_manager=db_manager  # تمرير db_manager للبوت
    )

    try:
        logger.info("جاري تشغيل البوت...")
        await bot.start(token)
    except discord.LoginFailure:
        logger.critical("فشل تسجيل الدخول إلى Discord. تحقق من صحة توكن البوت.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"حدث خطأ غير متوقع أثناء تشغيل البوت: {e}")
        sys.exit(1)
    finally:
        if not bot.is_closed():
            await bot.close()
        if db_manager:
            try:
                await db_manager.close()
            except:
                pass
        logger.info("تم إيقاف البوت وتنظيف الموارد.")

# --- نقطة الدخول الرئيسية للبرنامج ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت يدويًا.")
    except Exception as e:
        logger.critical(f"خطأ فادح في حلقة الأحداث الرئيسية: {e}")
        sys.exit(1)