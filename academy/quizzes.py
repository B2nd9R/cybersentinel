import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config import Config
from core.logger import get_security_logger
from core.database import db_manager

logger = get_security_logger()

class SecurityQuizzes:
    """نظام الاختبارات الأمنية التفاعلية"""
    
    def __init__(self):
        self.quizzes = {}
        self.active_quizzes = {}  # المستخدم -> معلومات الاختبار النشط
        self.user_scores = {}     # المستخدم -> النقاط
        self.cooldowns = {}       # المستخدم -> وقت آخر اختبار
        
    async def initialize(self):
        """تهيئة نظام الاختبارات"""
        try:
            await self._load_quizzes()
            logger.info("✅ تم تهيئة نظام الاختبارات الأمنية")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة نظام الاختبارات: {e}")
            
    async def _load_quizzes(self):
        """تحميل الاختبارات"""
        self.quizzes = {
            'basic_security': {
                'title': '🔒 اختبار الأمان الأساسي',
                'description': 'اختبر معرفتك بأساسيات الأمان الرقمي',
                'difficulty': 'easy',
                'time_limit': 300,  # 5 دقائق
                'questions': [
                    {
                        'question': 'ما هي أفضل طريقة لإنشاء كلمة مرور قوية؟',
                        'options': [
                            'استخدام اسمك وتاريخ ميلادك',
                            'استخدام مزيج من الأحرف والأرقام والرموز',
                            'استخدام كلمة واحدة بسيطة',
                            'استخدام نفس كلمة المرور لجميع الحسابات'
                        ],
                        'correct': 1,
                        'explanation': 'كلمة المرور القوية تحتوي على مزيج من الأحرف الكبيرة والصغيرة والأرقام والرموز'
                    },
                    {
                        'question': 'ما هو الخداع الإلكتروني (Phishing)؟',
                        'options': [
                            'نوع من الألعاب الإلكترونية',
                            'محاولة خداع للحصول على معلومات شخصية',
                            'طريقة لتسريع الإنترنت',
                            'برنامج لحماية الكمبيوتر'
                        ],
                        'correct': 1,
                        'explanation': 'الخداع الإلكتروني هو محاولة خداع المستخدمين للحصول على معلوماتهم الشخصية أو المالية'
                    },
                    {
                        'question': 'متى يجب عليك تحديث برامجك؟',
                        'options': [
                            'مرة واحدة في السنة',
                            'عندما تتوفر التحديثات الأمنية',
                            'فقط عند شراء جهاز جديد',
                            'لا حاجة للتحديث أبداً'
                        ],
                        'correct': 1,
                        'explanation': 'يجب تحديث البرامج فور توفر التحديثات الأمنية لحماية جهازك من الثغرات'
                    },
                    {
                        'question': 'ما هي المصادقة الثنائية؟',
                        'options': [
                            'استخدام كلمتي مرور',
                            'طبقة حماية إضافية تتطلب رمز تأكيد',
                            'نوع من البرامج الضارة',
                            'طريقة لحفظ كلمات المرور'
                        ],
                        'correct': 1,
                        'explanation': 'المصادقة الثنائية تضيف طبقة حماية إضافية عبر طلب رمز تأكيد من جهاز آخر'
                    },
                    {
                        'question': 'أيهما أكثر أماناً للتسوق الإلكتروني؟',
                        'options': [
                            'المواقع التي تبدأ بـ http://',
                            'المواقع التي تبدأ بـ https://',
                            'لا يوجد فرق',
                            'المواقع بدون أي بروتوكول'
                        ],
                        'correct': 1,
                        'explanation': 'المواقع التي تبدأ بـ https:// تستخدم التشفير لحماية بياناتك أثناء النقل'
                    }
                ]
            },
            'advanced_security': {
                'title': '🛡️ اختبار الأمان المتقدم',
                'description': 'اختبار للمستخدمين المتقدمين في الأمان الرقمي',
                'difficulty': 'hard',
                'time_limit': 600,  # 10 دقائق
                'questions': [
                    {
                        'question': 'ما هو VPN وما فائدته؟',
                        'options': [
                            'برنامج لتسريع الإنترنت',
                            'شبكة خاصة افتراضية لحماية الخصوصية',
                            'نوع من الفيروسات',
                            'طريقة لحفظ الملفات'
                        ],
                        'correct': 1,
                        'explanation': 'VPN يشفر اتصالك ويخفي عنوان IP الخاص بك لحماية خصوصيتك'
                    },
                    {
                        'question': 'ما هو التشفير من النهاية إلى النهاية؟',
                        'options': [
                            'تشفير يحمي الرسائل من المرسل إلى المستقبل فقط',
                            'تشفير يحمي الملفات على القرص الصلب',
                            'نوع من كلمات المرور',
                            'طريقة لضغط الملفات'
                        ],
                        'correct': 0,
                        'explanation': 'التشفير من النهاية إلى النهاية يضمن أن الرسالة مشفرة من المرسل حتى المستقبل'
                    },
                    {
                        'question': 'ما هو Zero-Day Attack؟',
                        'options': [
                            'هجوم يحدث في اليوم الأول من الشهر',
                            'هجوم يستغل ثغرة غير معروفة',
                            'هجوم بدون استخدام الإنترنت',
                            'هجوم يستغرق صفر ثانية'
                        ],
                        'correct': 1,
                        'explanation': 'Zero-Day Attack يستغل ثغرة أمنية لم يتم اكتشافها أو إصلاحها بعد'
                    }
                ]
            },
            'phishing_awareness': {
                'title': '🎣 اختبار الوعي بالخداع الإلكتروني',
                'description': 'تعلم كيفية اكتشاف محاولات الخداع الإلكتروني',
                'difficulty': 'medium',
                'time_limit': 400,  # 6.5 دقيقة
                'questions': [
                    {
                        'question': 'أي من هذه العلامات تدل على رسالة خداع إلكتروني؟',
                        'options': [
                            'طلب معلومات شخصية عبر البريد الإلكتروني',
                            'أخطاء إملائية ونحوية كثيرة',
                            'روابط مشبوهة أو مختصرة',
                            'جميع ما سبق'
                        ],
                        'correct': 3,
                        'explanation': 'جميع هذه العلامات تدل على محاولة خداع إلكتروني محتملة'
                    },
                    {
                        'question': 'ماذا تفعل إذا تلقيت رسالة تطلب منك تأكيد كلمة مرور حسابك المصرفي؟',
                        'options': [
                            'أرد على الرسالة بكلمة المرور',
                            'أتجاهل الرسالة وأتصل بالبنك مباشرة',
                            'أنقر على الرابط وأدخل المعلومات',
                            'أحول الرسالة لأصدقائي'
                        ],
                        'correct': 1,
                        'explanation': 'البنوك لا تطلب أبداً معلومات حساسة عبر البريد الإلكتروني، اتصل بهم مباشرة'
                    }
                ]
            }
        }
        
    async def get_available_quizzes(self) -> discord.Embed:
        """الحصول على قائمة الاختبارات المتاحة"""
        embed = discord.Embed(
            title="📝 الاختبارات المتاحة",
            description="اختر اختباراً لتقييم معرفتك الأمنية",
            color=Config.COLORS['info']
        )
        
        for quiz_id, quiz in self.quizzes.items():
            difficulty_emoji = {
                'easy': '🟢',
                'medium': '🟡', 
                'hard': '🔴'
            }.get(quiz['difficulty'], '⚪')
            
            embed.add_field(
                name=f"{difficulty_emoji} {quiz['title']}",
                value=f"{quiz['description']}\n📊 الصعوبة: {quiz['difficulty']}\n⏱️ الوقت: {quiz['time_limit']//60} دقائق\n❓ الأسئلة: {len(quiz['questions'])}",
                inline=False
            )
            
        return embed
        
    async def start_quiz(self, user_id: int, quiz_id: str) -> discord.Embed:
        """بدء اختبار"""
        # التحقق من وجود الاختبار
        if quiz_id not in self.quizzes:
            return discord.Embed(
                title="❌ خطأ",
                description="الاختبار غير موجود",
                color=Config.COLORS['error']
            )
            
        # التحقق من فترة الانتظار
        if await self._is_on_cooldown(user_id):
            remaining = await self._get_cooldown_remaining(user_id)
            return discord.Embed(
                title="⏰ انتظر قليلاً",
                description=f"يمكنك إجراء اختبار آخر بعد {remaining} ثانية",
                color=Config.COLORS['warning']
            )
            
        # التحقق من وجود اختبار نشط
        if user_id in self.active_quizzes:
            return discord.Embed(
                title="📝 اختبار نشط",
                description="لديك اختبار نشط بالفعل. أكمله أولاً أو استخدم `!quiz_cancel` لإلغائه",
                color=Config.COLORS['warning']
            )

        # إنشاء اختبار جديد
        quiz_data = self.quizzes.get(quiz_id)
        if not quiz_data:
            return discord.Embed(
                title="❌ خطأ",
                description="نوع الاختبار غير صالح",
                color=Config.COLORS['error']
            )

        # بدء الاختبار
        self.active_quizzes[user_id] = {
            'quiz_type': quiz_id,
            'current_question': 0,
            'correct_answers': 0,
            'start_time': datetime.now(),
            'time_limit': quiz_data['time_limit']
        }

        return self._create_question_embed(user_id)