import os
from typing import Dict, Any
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

class Config:
    """إعدادات البوت الرئيسية
    
    يحتوي على جميع إعدادات البوت القابلة للتخصيص، مع التحقق من صحة القيم
    وتوفير قيم افتراضية مناسبة.
    """
    
    # Discord Configuration - إصلاح المتغيرات
    DISCORD_TOKEN: str = os.getenv('DISCORD_BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
    DISCORD_BOT_TOKEN: str = os.getenv('DISCORD_BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
    BOT_PREFIX: str = os.getenv('BOT_PREFIX', '!')  # إضافة BOT_PREFIX
    COMMAND_PREFIX: str = os.getenv('COMMAND_PREFIX', '!')
    OWNER_ID: int = int(os.getenv('OWNER_ID', 0)) if os.getenv('OWNER_ID') else 0
    
    # API Keys
    VIRUSTOTAL_API_KEY: str = os.getenv('VIRUSTOTAL_API_KEY')

    # Web Dashboard Configuration
    WEB_HOST: str = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT: int = int(os.getenv('WEB_PORT', '8000'))
    ADMIN_USERNAME: str = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD: str = os.getenv('ADMIN_PASSWORD', 'changeme')
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///security_bot.db')
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'security_bot.db')  # إضافة مسار قاعدة البيانات
    
    # Security Settings
    DEFAULT_PROTECTION_LEVEL: int = int(os.getenv('DEFAULT_PROTECTION_LEVEL', 2))
    MAX_DANGER_POINTS: int = int(os.getenv('MAX_DANGER_POINTS', 10))
    LINK_SCAN_TIMEOUT: int = int(os.getenv('LINK_SCAN_TIMEOUT', 30))
    
    # Rate Limiting
    MAX_MESSAGES_PER_MINUTE: int = int(os.getenv('MAX_MESSAGES_PER_MINUTE', 10))
    RAID_DETECTION_THRESHOLD: int = int(os.getenv('RAID_DETECTION_THRESHOLD', 5))
    RAID_DETECTION_WINDOW: int = int(os.getenv('RAID_DETECTION_WINDOW', 120))
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'bot.log')
    
    # Admin Settings
    ADMIN_ROLE_NAME: str = os.getenv('ADMIN_ROLE_NAME', 'Security Admin')
    
    # File Types Restrictions
    DANGEROUS_FILE_EXTENSIONS: list = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.pkg', '.dmg', '.msi', '.ps1'
    ]
    
    # Malicious Keywords
    SUSPICIOUS_KEYWORDS: list = [
        'free nitro', 'discord gift', 'free bitcoin', 'click here to claim',
        'verify account', 'suspended account', 'urgent action required',
        'congratulations you won', 'claim your prize', 'limited time offer'
    ]
    
    # Embed Colors
    COLORS: Dict[str, int] = {
        'success': 0x00ff00,
        'warning': 0xffff00,
        'error': 0xff0000,
        'info': 0x00ffff,
        'security': 0xff6b6b
    }
    
    # Security Levels
    PROTECTION_LEVELS: Dict[int, str] = {
        1: 'Basic',      # فحص أساسي فقط
        2: 'Standard',   # فحص شامل + تحذيرات
        3: 'Advanced',   # فحص شامل + إجراءات تلقائية
        4: 'Maximum'     # حماية قصوى + حظر فوري
    }
    
    @classmethod
    def get_protection_level_name(cls, level: int) -> str:
        """الحصول على اسم مستوى الحماية"""
        return cls.PROTECTION_LEVELS.get(level, 'Unknown')
    
    @classmethod
    def validate(cls) -> bool:
        """التحقق من صحة الإعدادات المطلوبة
        
        Returns:
            bool: True إذا كانت جميع الإعدادات المطلوبة صحيحة
        
        Raises:
            ValueError: إذا كان هناك إعداد مطلوب مفقود أو غير صحيح
        """
        if not cls.DISCORD_TOKEN and not cls.DISCORD_BOT_TOKEN:
            raise ValueError("DISCORD_BOT_TOKEN مطلوب في ملف .env")
            
        if not cls.VIRUSTOTAL_API_KEY:
            print("تحذير: VIRUSTOTAL_API_KEY غير موجود - فحص الروابط سيكون محدود")
            
        if cls.DEFAULT_PROTECTION_LEVEL not in cls.PROTECTION_LEVELS:
            raise ValueError(f"DEFAULT_PROTECTION_LEVEL يجب أن يكون بين 1 و {len(cls.PROTECTION_LEVELS)}")
        
        return True