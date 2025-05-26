import aiofiles
import aiosqlite
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from core.logger import get_database_logger

logger = get_database_logger()

class DatabaseManager:
    """مدير قاعدة البيانات الرئيسي"""
    
    def __init__(self, db_path: str = "security_bot.db"):
        self.db_path = db_path
        self.initialized = False
    
    async def initialize(self):
        """إنشاء قاعدة البيانات والجداول"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await self._create_tables(db)
                await self._insert_default_data(db)
                await db.commit()
            
            self.initialized = True
            logger.info("✅ تم إنشاء قاعدة البيانات بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
            raise
    
    async def _create_tables(self, db: aiosqlite.Connection):
        """إنشاء جداول قاعدة البيانات"""
        
        # جدول إعدادات السيرفرات
        await db.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                admin_channel_id INTEGER,
                protection_level INTEGER DEFAULT 2,
                auto_ban_threshold INTEGER DEFAULT 10,
                link_scan_enabled BOOLEAN DEFAULT 1,
                anti_raid_enabled BOOLEAN DEFAULT 1,
                behavior_monitoring BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول التهديدات
        await db.execute('''
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                threat_type TEXT NOT NULL,
                content TEXT,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'detected',
                action_taken TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                resolved_by INTEGER
            )
        ''')
        
        # جدول الروابط المفحوصة
        await db.execute('''
            CREATE TABLE IF NOT EXISTS scanned_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                is_malicious BOOLEAN NOT NULL,
                scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                virustotal_score INTEGER DEFAULT 0,
                scan_engines TEXT,
                threat_names TEXT
            )
        ''')
        
        # جدول نقاط الخطر للمستخدمين
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_danger_scores (
                user_id INTEGER,
                guild_id INTEGER,
                danger_points INTEGER DEFAULT 0,
                total_warnings INTEGER DEFAULT 0,
                last_warning DATETIME,
                last_violation DATETIME,
                status TEXT DEFAULT 'active',
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        # جدول البلاغات
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                reporter_id INTEGER NOT NULL,
                reported_user_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                evidence TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                handled_by INTEGER,
                handled_at DATETIME,
                action_taken TEXT
            )
        ''')
        
        # جدول إحصائيات الأمان
        await db.execute('''
            CREATE TABLE IF NOT EXISTS security_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                stat_date DATE NOT NULL,
                threats_detected INTEGER DEFAULT 0,
                links_scanned INTEGER DEFAULT 0,
                malicious_links_blocked INTEGER DEFAULT 0,
                users_warned INTEGER DEFAULT 0,
                users_banned INTEGER DEFAULT 0,
                raids_prevented INTEGER DEFAULT 0,
                UNIQUE(guild_id, stat_date)
            )
        ''')
        
        # إنشاء الفهارس لتسريع الاستعلامات
        await db.execute('CREATE INDEX IF NOT EXISTS idx_threats_guild_user ON threats(guild_id, user_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_threats_timestamp ON threats(timestamp)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_scanned_links_hash ON scanned_links(url_hash)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_user_scores_guild ON user_danger_scores(guild_id)')
    
    async def _insert_default_data(self, db: aiosqlite.Connection):
        """إدراج البيانات الافتراضية"""
        # بيانات افتراضية لاحقًا إذا احتجنا
        pass
    
    # وظائف إعدادات السيرفر
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """الحصول على إعدادات السيرفر"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM guild_settings WHERE guild_id = ?', 
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    # إنشاء إعدادات افتراضية
                    return await self.create_default_guild_settings(guild_id)
    
    async def create_default_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """إنشاء إعدادات افتراضية للسيرفر"""
        default_settings = {
            'guild_id': guild_id,
            'admin_channel_id': None,
            'protection_level': 2,
            'auto_ban_threshold': 10,
            'link_scan_enabled': True,
            'anti_raid_enabled': True,
            'behavior_monitoring': True
        }
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, protection_level, auto_ban_threshold, link_scan_enabled, anti_raid_enabled, behavior_monitoring)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (guild_id, 2, 10, 1, 1, 1))
            await db.commit()
        
        return default_settings
    
    async def update_guild_settings(self, guild_id: int, **kwargs):
        """تحديث إعدادات السيرفر"""
        if not kwargs:
            return
        
        # إنشاء استعلام التحديث الديناميكي
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [guild_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f'''
                UPDATE guild_settings 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE guild_id = ?
            ''', values)
            await db.commit()
    
    # وظائف التهديدات
    async def add_threat(self, guild_id: int, user_id: int, threat_type: str, 
                        content: str = None, severity: str = 'medium') -> int:
        """إضافة تهديد جديد"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO threats (guild_id, user_id, threat_type, content, severity)
                VALUES (?, ?, ?, ?, ?)
            ''', (guild_id, user_id, threat_type, content, severity))
            
            threat_id = cursor.lastrowid
            await db.commit()
            
            # تحديث الإحصائيات
            await self._update_daily_stats(db, guild_id, 'threats_detected', 1)
            
            logger.info(f"🚨 تم تسجيل تهديد جديد: {threat_type} من المستخدم {user_id}")
            return threat_id
    
    async def get_user_threats(self, guild_id: int, user_id: int, 
                              days: int = 30) -> List[Dict[str, Any]]:
        """الحصول على تهديدات المستخدم في فترة معينة"""
        since_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT * FROM threats 
                WHERE guild_id = ? AND user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (guild_id, user_id, since_date)) as cursor:
                
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    
    # وظائف نقاط الخطر
    async def add_danger_points(self, guild_id: int, user_id: int, points: int):
        """إضافة نقاط خطر للمستخدم"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO user_danger_scores 
                (user_id, guild_id, danger_points, total_warnings, last_warning)
                VALUES (
                    ?, ?, 
                    COALESCE((SELECT danger_points FROM user_danger_scores WHERE user_id = ? AND guild_id = ?), 0) + ?,
                    COALESCE((SELECT total_warnings FROM user_danger_scores WHERE user_id = ? AND guild_id = ?), 0) + 1,
                    CURRENT_TIMESTAMP
                )
            ''', (user_id, guild_id, user_id, guild_id, points, user_id, guild_id))
            await db.commit()
    
    async def get_user_danger_score(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        """الحصول على نقاط خطر المستخدم"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT * FROM user_danger_scores 
                WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id)) as cursor:
                
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    return {'danger_points': 0, 'total_warnings': 0}
    
    # وظائف الروابط المفحوصة
    async def add_scanned_link(self, url_hash: str, original_url: str, 
                              is_malicious: bool, vt_score: int = 0, 
                              scan_engines: str = None, threat_names: str = None):
        """إضافة رابط مفحوص"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO scanned_links 
                (url_hash, original_url, is_malicious, virustotal_score, scan_engines, threat_names)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url_hash, original_url, is_malicious, vt_score, scan_engines, threat_names))
            await db.commit()
    
    async def get_scanned_link(self, url_hash: str) -> Optional[Dict[str, Any]]:
        """الحصول على نتيجة فحص رابط محفوظ"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT * FROM scanned_links WHERE url_hash = ?
            ''', (url_hash,)) as cursor:
                
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
    
    # وظائف الإحصائيات
    async def _update_daily_stats(self, db: aiosqlite.Connection, guild_id: int, 
                                 stat_name: str, increment: int = 1):
        """تحديث الإحصائيات اليومية"""
        today = datetime.now().date()
        
        await db.execute(f'''
            INSERT OR REPLACE INTO security_stats 
            (guild_id, stat_date, {stat_name})
            VALUES (
                ?, ?, 
                COALESCE((SELECT {stat_name} FROM security_stats WHERE guild_id = ? AND stat_date = ?), 0) + ?
            )
        ''', (guild_id, today, guild_id, today, increment))
    
    async def get_security_stats(self, guild_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """الحصول على إحصائيات الأمان لفترة معينة"""
        since_date = datetime.now().date() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT * FROM security_stats 
                WHERE guild_id = ? AND stat_date >= ?
                ORDER BY stat_date DESC
            ''', (guild_id, since_date)) as cursor:
                
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    
    async def get_total_stats(self, guild_id: int) -> Dict[str, int]:
        """الحصول على إجمالي الإحصائيات"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT 
                    SUM(threats_detected) as total_threats,
                    SUM(links_scanned) as total_links_scanned,
                    SUM(malicious_links_blocked) as total_malicious_blocked,
                    SUM(users_warned) as total_users_warned,
                    SUM(users_banned) as total_users_banned,
                    SUM(raids_prevented) as total_raids_prevented
                FROM security_stats 
                WHERE guild_id = ?
            ''', (guild_id,)) as cursor:
                
                row = await cursor.fetchone()
                if row:
                    return {
                        'total_threats': row[0] or 0,
                        'total_links_scanned': row[1] or 0,
                        'total_malicious_blocked': row[2] or 0,
                        'total_users_warned': row[3] or 0,
                        'total_users_banned': row[4] or 0,
                        'total_raids_prevented': row[5] or 0
                    }
                return {}
    
    # وظائف البلاغات
    async def create_report(self, guild_id: int, reporter_id: int, reported_user_id: int, 
                           reason: str, evidence: str = None) -> int:
        """إنشاء بلاغ جديد"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO reports (guild_id, reporter_id, reported_user_id, reason, evidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (guild_id, reporter_id, reported_user_id, reason, evidence))
            
            report_id = cursor.lastrowid
            await db.commit()
            
            logger.info(f"📝 تم إنشاء بلاغ جديد #{report_id} في السيرفر {guild_id}")
            return report_id
    
    async def get_pending_reports(self, guild_id: int) -> List[Dict[str, Any]]:
        """الحصول على البلاغات المعلقة"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT * FROM reports 
                WHERE guild_id = ? AND status = 'pending'
                ORDER BY created_at ASC
            ''', (guild_id,)) as cursor:
                
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    
    async def handle_report(self, report_id: int, handler_id: int, action_taken: str):
        """معالجة بلاغ"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE reports 
                SET status = 'handled', handled_by = ?, handled_at = CURRENT_TIMESTAMP, action_taken = ?
                WHERE id = ?
            ''', (handler_id, action_taken, report_id))
            await db.commit()
    
    # وظائف الصيانة
    async def cleanup_old_data(self, days: int = 90):
        """تنظيف البيانات القديمة"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # حذف التهديدات القديمة المحلولة
            await db.execute('''
                DELETE FROM threats 
                WHERE timestamp < ? AND status = 'resolved'
            ''', (cutoff_date,))
            
            # حذف الروابط المفحوصة القديمة
            await db.execute('''
                DELETE FROM scanned_links 
                WHERE scan_date < ?
            ''', (cutoff_date,))
            
            # حذف الإحصائيات القديمة
            old_stats_date = datetime.now().date() - timedelta(days=days)
            await db.execute('''
                DELETE FROM security_stats 
                WHERE stat_date < ?
            ''', (old_stats_date,))
            
            await db.commit()
            logger.info(f"🧹 تم تنظيف البيانات الأقدم من {days} يوم")
    
    async def get_database_stats(self) -> Dict[str, int]:
        """الحصول على إحصائيات قاعدة البيانات"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # عدد السيرفرات
            async with db.execute('SELECT COUNT(*) FROM guild_settings') as cursor:
                stats['guilds'] = (await cursor.fetchone())[0]
            
            # عدد التهديدات
            async with db.execute('SELECT COUNT(*) FROM threats') as cursor:
                stats['threats'] = (await cursor.fetchone())[0]
            
            # عدد الروابط المفحوصة
            async with db.execute('SELECT COUNT(*) FROM scanned_links') as cursor:
                stats['scanned_links'] = (await cursor.fetchone())[0]
            
            # عدد البلاغات
            async with db.execute('SELECT COUNT(*) FROM reports') as cursor:
                stats['reports'] = (await cursor.fetchone())[0]
            
            # عدد المستخدمين المراقبين
            async with db.execute('SELECT COUNT(*) FROM user_danger_scores') as cursor:
                stats['monitored_users'] = (await cursor.fetchone())[0]
            
            return stats
    
    async def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if hasattr(self, 'db') and self.db:
            await self.db.close()
            logger.info("🔒 تم إغلاق الاتصال بقاعدة البيانات")

# إنشاء مثيل وحيد من مدير قاعدة البيانات
db_manager = DatabaseManager()