import discord
from discord.ext import commands
import json
import random
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from config import Config
from core.logger import get_security_logger
from core.database import db_manager

logger = get_security_logger()

class SecurityEducation:
    """نظام التعليم الأمني التفاعلي"""
    
    def __init__(self):
        self.education_data = {}
        self.user_progress = {}
        self.courses = {}
        
    async def initialize(self):
        """تهيئة نظام التعليم"""
        try:
            await self._load_education_content()
            await self._setup_courses()
            logger.info("✅ تم تهيئة نظام التعليم الأمني")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة نظام التعليم: {e}")
            
    async def _load_education_content(self):
        """تحميل المحتوى التعليمي"""
        self.education_data = {
            'courses': {
                'basic_security': {
                    'title': '🔒 أساسيات الأمان الرقمي',
                    'description': 'تعلم الأساسيات المهمة لحماية نفسك على الإنترنت',
                    'lessons': [
                        {
                            'id': 'passwords',
                            'title': 'كلمات المرور القوية',
                            'content': 'كيفية إنشاء كلمات مرور قوية وآمنة',
                            'duration': 10
                        },
                        {
                            'id': 'phishing',
                            'title': 'التعرف على الخداع الإلكتروني',
                            'content': 'كيفية اكتشاف رسائل الخداع والمواقع المزيفة',
                            'duration': 15
                        },
                        {
                            'id': 'social_media',
                            'title': 'أمان وسائل التواصل',
                            'content': 'حماية حساباتك على منصات التواصل الاجتماعي',
                            'duration': 12
                        }
                    ]
                },
                'advanced_security': {
                    'title': '🛡️ الأمان المتقدم',
                    'description': 'مواضيع متقدمة في الأمان الرقمي',
                    'lessons': [
                        {
                            'id': 'encryption',
                            'title': 'التشفير والخصوصية',
                            'content': 'فهم أساسيات التشفير وحماية البيانات',
                            'duration': 20
                        },
                        {
                            'id': 'network_security',
                            'title': 'أمان الشبكات',
                            'content': 'حماية اتصالاتك وشبكاتك المنزلية',
                            'duration': 25
                        }
                    ]
                }
            },
            'tips': {
                'daily': [
                    '🔐 استخدم كلمة مرور مختلفة لكل حساب',
                    '🔍 تحقق من الروابط قبل النقر عليها',
                    '📱 فعّل المصادقة الثنائية على جميع حساباتك',
                    '🚫 لا تشارك معلوماتك الشخصية مع الغرباء',
                    '💻 حدّث برامجك ونظام التشغيل بانتظام'
                ]
            }
        }
        
    async def _setup_courses(self):
        """إعداد الدورات التعليمية"""
        self.courses = self.education_data['courses']
        
    async def get_course_list(self) -> discord.Embed:
        """الحصول على قائمة الدورات المتاحة"""
        embed = discord.Embed(
            title="📚 الدورات التعليمية المتاحة",
            description="اختر دورة لبدء التعلم",
            color=Config.COLORS['info']
        )
        
        for course_id, course in self.courses.items():
            lessons_count = len(course['lessons'])
            total_duration = sum(lesson['duration'] for lesson in course['lessons'])
            
            embed.add_field(
                name=course['title'],
                value=f"{course['description']}\n📖 {lessons_count} دروس | ⏱️ {total_duration} دقيقة",
                inline=False
            )
            
        return embed
        
    async def start_course(self, user_id: int, course_id: str) -> discord.Embed:
        """بدء دورة تعليمية"""
        if course_id not in self.courses:
            return discord.Embed(
                title="❌ خطأ",
                description="الدورة غير موجودة",
                color=Config.COLORS['error']
            )
            
        course = self.courses[course_id]
        
        # تسجيل بداية الدورة
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
            
        self.user_progress[user_id][course_id] = {
            'started_at': datetime.now(),
            'current_lesson': 0,
            'completed_lessons': [],
            'status': 'in_progress'
        }
        
        embed = discord.Embed(
            title=f"🎓 بدء الدورة: {course['title']}",
            description=course['description'],
            color=Config.COLORS['success']
        )
        
        first_lesson = course['lessons'][0]
        embed.add_field(
            name="📖 الدرس الأول",
            value=f"**{first_lesson['title']}**\n{first_lesson['content']}",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ المدة المتوقعة",
            value=f"{first_lesson['duration']} دقيقة",
            inline=True
        )
        
        return embed
        
    async def get_lesson(self, user_id: int, course_id: str, lesson_index: int) -> discord.Embed:
        """الحصول على درس معين"""
        if course_id not in self.courses:
            return discord.Embed(
                title="❌ خطأ",
                description="الدورة غير موجودة",
                color=Config.COLORS['error']
            )
            
        course = self.courses[course_id]
        
        if lesson_index >= len(course['lessons']):
            return discord.Embed(
                title="🎉 تهانينا!",
                description="لقد أكملت جميع دروس هذه الدورة",
                color=Config.COLORS['success']
            )
            
        lesson = course['lessons'][lesson_index]
        
        embed = discord.Embed(
            title=f"📖 {lesson['title']}",
            description=lesson['content'],
            color=Config.COLORS['info']
        )
        
        embed.add_field(
            name="📊 التقدم",
            value=f"الدرس {lesson_index + 1} من {len(course['lessons'])}",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ المدة",
            value=f"{lesson['duration']} دقيقة",
            inline=True
        )
        
        return embed
        
    async def complete_lesson(self, user_id: int, course_id: str, lesson_index: int) -> discord.Embed:
        """إكمال درس"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
            
        if course_id not in self.user_progress[user_id]:
            self.user_progress[user_id][course_id] = {
                'started_at': datetime.now(),
                'current_lesson': 0,
                'completed_lessons': [],
                'status': 'in_progress'
            }
            
        progress = self.user_progress[user_id][course_id]
        
        if lesson_index not in progress['completed_lessons']:
            progress['completed_lessons'].append(lesson_index)
            progress['current_lesson'] = lesson_index + 1
            
        course = self.courses[course_id]
        total_lessons = len(course['lessons'])
        completed_count = len(progress['completed_lessons'])
        
        embed = discord.Embed(
            title="✅ تم إكمال الدرس!",
            description=f"أحسنت! لقد أكملت الدرس بنجاح",
            color=Config.COLORS['success']
        )
        
        embed.add_field(
            name="📊 التقدم الإجمالي",
            value=f"{completed_count}/{total_lessons} دروس مكتملة ({completed_count/total_lessons*100:.1f}%)",
            inline=False
        )
        
        # إذا اكتمل جميع الدروس
        if completed_count == total_lessons:
            progress['status'] = 'completed'
            progress['completed_at'] = datetime.now()
            
            embed.add_field(
                name="🎉 تهانينا!",
                value="لقد أكملت الدورة بالكامل! حصلت على شهادة إتمام",
                inline=False
            )
            
        return embed
        
    async def get_user_progress(self, user_id: int) -> discord.Embed:
        """الحصول على تقدم المستخدم"""
        embed = discord.Embed(
            title="📊 تقدمك التعليمي",
            description="إليك ملخص تقدمك في الدورات",
            color=Config.COLORS['info']
        )
        
        if user_id not in self.user_progress or not self.user_progress[user_id]:
            embed.add_field(
                name="📚 لم تبدأ أي دورة بعد",
                value="استخدم `!courses` لرؤية الدورات المتاحة",
                inline=False
            )
            return embed
            
        for course_id, progress in self.user_progress[user_id].items():
            if course_id in self.courses:
                course = self.courses[course_id]
                total_lessons = len(course['lessons'])
                completed_count = len(progress['completed_lessons'])
                
                status_emoji = "✅" if progress['status'] == 'completed' else "📖"
                progress_percent = completed_count / total_lessons * 100
                
                embed.add_field(
                    name=f"{status_emoji} {course['title']}",
                    value=f"التقدم: {completed_count}/{total_lessons} ({progress_percent:.1f}%)\nالحالة: {progress['status']}",
                    inline=True
                )
                
        return embed
        
    async def get_daily_tip(self) -> str:
        """الحصول على نصيحة يومية"""
        tips = self.education_data['tips']['daily']
        return random.choice(tips)
        
    async def search_content(self, query: str) -> discord.Embed:
        """البحث في المحتوى التعليمي"""
        results = []
        query_lower = query.lower()
        
        for course_id, course in self.courses.items():
            # البحث في عنوان الدورة
            if query_lower in course['title'].lower() or query_lower in course['description'].lower():
                results.append({
                    'type': 'course',
                    'title': course['title'],
                    'description': course['description'],
                    'id': course_id
                })
                
            # البحث في الدروس
            for lesson in course['lessons']:
                if query_lower in lesson['title'].lower() or query_lower in lesson['content'].lower():
                    results.append({
                        'type': 'lesson',
                        'title': lesson['title'],
                        'description': lesson['content'][:100] + '...',
                        'course': course['title']
                    })
                    
        embed = discord.Embed(
            title=f"🔍 نتائج البحث: {query}",
            color=Config.COLORS['info']
        )
        
        if not results:
            embed.description = "لم يتم العثور على نتائج"
        else:
            for i, result in enumerate(results[:5]):  # أول 5 نتائج
                if result['type'] == 'course':
                    embed.add_field(
                        name=f"📚 {result['title']}",
                        value=result['description'],
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"📖 {result['title']}",
                        value=f"من دورة: {result['course']}\n{result['description']}",
                        inline=False
                    )
                    
        return embed