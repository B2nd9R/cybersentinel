"""
وحدة الأوامر - CyberSentinel Discord Bot

تحتوي هذه الوحدة على جميع أوامر البوت المقسمة حسب الفئات:
- security: أوامر الأمان والحماية
- admin: أوامر الإدارة
- reports: أوامر التقارير والإحصائيات
"""

from .security import SecurityCommands
from .admin import AdminCommands
from .reports import ReportsCommands
from .general import GeneralCommands

__all__ = [
    'SecurityCommands',
    'AdminCommands', 
    'ReportsCommands',
    'GeneralCommands'  # إضافة هذا السطر
]

# معلومات الوحدة
__version__ = '1.0.0'
__author__ = 'CyberSentinel Team'
__description__ = 'Discord Bot Commands Module for Security and Administration'

# قائمة جميع الأوامر المتاحة
COMMANDS_INFO = {
    'security': {
        'description': 'أوامر الأمان والحماية',
        'commands': [
            'scan_url',
            'user_info', 
            'warn_user',
            'security_scan',
            'lockdown',
            'clear_threats',
            'protection_level',
            'quarantine'
        ]
    },
    'admin': {
        'description': 'أوامر الإدارة',
        'commands': [
            'kick',
            'ban',
            'unban',
            'mute',
            'unmute',
            'purge',
            'slowmode',
            'role_add',
            'role_remove'
        ]
    },
    'reports': {
        'description': 'أوامر التقارير والإحصائيات',
        'commands': [
            'security_report',
            'threat_log',
            'export_data',
            'stats'
        ]
    }
}

def get_all_commands():
    """إرجاع قائمة بجميع الأوامر المتاحة"""
    all_commands = []
    for category, info in COMMANDS_INFO.items():
        all_commands.extend(info['commands'])
    return all_commands

def get_commands_by_category(category):
    """إرجاع أوامر فئة محددة"""
    return COMMANDS_INFO.get(category, {}).get('commands', [])

def get_command_info(command_name):
    """إرجاع معلومات أمر محدد"""
    for category, info in COMMANDS_INFO.items():
        if command_name in info['commands']:
            return {
                'category': category,
                'description': info['description']
            }
    return None

# دالة لتحميل جميع الأوامر
# تحديث COMMANDS_INFO
COMMANDS_INFO['General'] = {
    'description': 'الأوامر العامة للبوت',
    'commands': {
        'help': 'عرض قائمة الأوامر المتاحة',
        'ping': 'التحقق من زمن استجابة البوت',
        'info': 'عرض معلومات عن البوت'
    }
}

def setup_all_commands(bot):
    """تحميل جميع الأوامر للبوت"""
    # إضافة الأوامر العامة
    if GeneralCommands:
        bot.add_cog(GeneralCommands(bot))
    
    try:
        # تحميل أوامر الأمان
        bot.add_cog(SecurityCommands(bot))
        print("✅ تم تحميل أوامر الأمان")
        
        # تحميل أوامر الإدارة
        bot.add_cog(AdminCommands(bot))
        print("✅ تم تحميل أوامر الإدارة")
        
        # تحميل أوامر التقارير
        bot.add_cog(ReportsCommands(bot))
        print("✅ تم تحميل أوامر التقارير")
        
        print(f"🎉 تم تحميل {len(get_all_commands())} أمر بنجاح")
        
    except Exception as e:
        print(f"❌ خطأ في تحميل الأوامر: {e}")
        raise