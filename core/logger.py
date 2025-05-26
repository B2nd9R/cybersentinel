import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime
from config import Config

class SecurityLogger:
    def __init__(self, name: str = 'SecurityBot'):
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """إعداد نظام التسجيل مع الدوران والتنسيق المتقدم"""
        # إنشاء مجلد اللوجات
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # تنسيق متقدم للرسائل
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ملف يومي مع الدوران
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            logs_dir / 'security.log',
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        daily_handler.setFormatter(formatter)
        
        # ملف للأحداث الأمنية الهامة
        security_handler = logging.FileHandler(
            logs_dir / 'security_events.log',
            encoding='utf-8'
        )
        security_handler.setFormatter(formatter)
        security_handler.setLevel(logging.WARNING)
        
        # مخرجات الكونسول
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # إضافة المعالجات
        self.logger.addHandler(daily_handler)
        self.logger.addHandler(security_handler)
        self.logger.addHandler(console_handler)
        
        # مستوى التسجيل
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    def log_security_event(self, event_type: str, details: dict, level: str = 'WARNING'):
        """تسجيل حدث أمني مع التفاصيل"""
        log_level = getattr(logging, level.upper())
        event_time = datetime.now().isoformat()
        
        message = f"Security Event [{event_type}] at {event_time}\n"
        message += "Details:\n"
        for key, value in details.items():
            message += f"  {key}: {value}\n"
        
        self.logger.log(log_level, message)
    
    def error(self, message, *args, **kwargs):
        """تسجيل رسالة خطأ"""
        self.logger.error(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """تسجيل رسالة تحذير"""
        self.logger.warning(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """تسجيل رسالة معلومات"""
        self.logger.info(message, *args, **kwargs)
    
    def debug(self, message, *args, **kwargs):
        """تسجيل رسالة تصحيح"""
        self.logger.debug(message, *args, **kwargs)

# إنشاء مثيل عام
logger = SecurityLogger()

def setup_logger(name: str = 'SecurityBot') -> logging.Logger:
    """إعداد وإرجاع logger - دالة للتوافق مع الكود الموجود"""
    security_logger = SecurityLogger(name)
    return security_logger.logger

def get_security_logger() -> SecurityLogger:
    """الحصول على مثيل اللوجر"""
    return logger

def get_database_logger() -> logging.Logger:
    """الحصول على logger خاص بقاعدة البيانات - إضافة الدالة المفقودة"""
    database_logger = SecurityLogger('DatabaseManager')
    return database_logger.logger

def log_security_event(event_type: str, details: dict, level: str = 'WARNING'):
    """دالة مساعدة لتسجيل الأحداث الأمنية"""
    logger.log_security_event(event_type, details, level)

def setup_logging():
    """إعداد نظام التسجيل العام - للتوافق مع main.py"""
    # إعداد نظام التسجيل الأساسي
    logging.basicConfig(
        level=getattr(logging, getattr(Config, 'LOG_LEVEL', 'INFO')),
        format='%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # إنشاء مجلد اللوجات
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    return logging.getLogger(__name__)