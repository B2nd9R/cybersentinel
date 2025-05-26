"""
API Module - وحدة الـ APIs الخارجية
تحتوي على جميع التكاملات مع الخدمات الخارجية
"""

from .virustotal import VirusTotalAPI
from .external_apis import ExternalAPIManager

__all__ = [
    'VirusTotalAPI',
    'ExternalAPIManager'
]