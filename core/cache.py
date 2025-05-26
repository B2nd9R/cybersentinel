from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_config = {
            'url_scan': {'ttl': 3600},  # 1 hour
            'user_info': {'ttl': 1800},  # 30 minutes
            'guild_settings': {'ttl': 300}  # 5 minutes
        }
    
    async def get(self, cache_type: str, key: str) -> Optional[Any]:
        """استرجاع قيمة من الكاش"""
        # فحص الكاش في الذاكرة
        if cache_type in self.memory_cache and key in self.memory_cache[cache_type]:
            data = self.memory_cache[cache_type][key]
            if not self._is_expired(data['timestamp'], cache_type):
                return data['value']
        
        # فحص الكاش في الملفات
        cache_file = self.cache_dir / f"{cache_type}_{key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                if not self._is_expired(data['timestamp'], cache_type):
                    # تحديث الكاش في الذاكرة
                    self._update_memory_cache(cache_type, key, data)
                    return data['value']
            except Exception:
                pass
        
        return None
    
    async def set(self, cache_type: str, key: str, value: Any):
        """تخزين قيمة في الكاش"""
        data = {
            'value': value,
            'timestamp': datetime.now().timestamp()
        }
        
        # تحديث الكاش في الذاكرة
        if cache_type not in self.memory_cache:
            self.memory_cache[cache_type] = {}
        self.memory_cache[cache_type][key] = data
        
        # تخزين في الملفات
        cache_file = self.cache_dir / f"{cache_type}_{key}.json"
        try:
            cache_file.write_text(json.dumps(data))
        except Exception:
            pass
    
    def _is_expired(self, timestamp: float, cache_type: str) -> bool:
        """التحقق من انتهاء صلاحية الكاش"""
        ttl = self.cache_config.get(cache_type, {}).get('ttl', 3600)
        return (datetime.now().timestamp() - timestamp) > ttl
    
    def _update_memory_cache(self, cache_type: str, key: str, data: dict):
        """تحديث الكاش في الذاكرة"""
        if cache_type not in self.memory_cache:
            self.memory_cache[cache_type] = {}
        self.memory_cache[cache_type][key] = data
    
    async def cleanup(self):
        """تنظيف الكاش القديم"""
        # تنظيف الكاش في الذاكرة
        for cache_type in list(self.memory_cache.keys()):
            for key in list(self.memory_cache[cache_type].keys()):
                data = self.memory_cache[cache_type][key]
                if self._is_expired(data['timestamp'], cache_type):
                    del self.memory_cache[cache_type][key]
        
        # تنظيف ملفات الكاش
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text())
                cache_type = cache_file.stem.split('_')[0]
                if self._is_expired(data['timestamp'], cache_type):
                    cache_file.unlink()
            except Exception:
                pass

# إنشاء مثيل عام
cache_manager = CacheManager()