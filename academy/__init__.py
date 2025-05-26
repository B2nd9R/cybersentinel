"""
وحدة الأكاديمية الأمنية - CyberSentinel Discord Bot

تحتوي هذه الوحدة على:
- نصائح الأمان والتوعية
- الاختبارات التفاعلية
- المواد التعليمية
"""

from .security_tips import SecurityAcademy
from .education import SecurityEducation
from .quizzes import SecurityQuizzes

__all__ = [
    'SecurityAcademy',
    'SecurityEducation', 
    'SecurityQuizzes'
]

# معلومات الوحدة
__version__ = '1.0.0'
__author__ = 'CyberSentinel Team'
__description__ = 'Security Academy Module for Discord Bot Education'

# إعدادات الأكاديمية
ACADEMY_CONFIG = {
    'daily_tips_enabled': True,
    'quiz_cooldown': 300,  # 5 دقائق
    'education_channels': ['security', 'education', 'academy'],
    'max_quiz_attempts': 3,
    'tip_categories': [
        'password_security',
        'phishing_awareness', 
        'social_engineering',
        'malware_protection',
        'privacy_settings',
        'two_factor_auth'
    ]
}