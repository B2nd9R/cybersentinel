<div align="center">

# 🛡️ CyberSentinel Discord Bot

[![Discord](https://img.shields.io/discord/YOUR_SERVER_ID?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://discord.gg/your-invite)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.0%2B-blue?logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Stars](https://img.shields.io/github/stars/B2nd9R/cybersentinel?style=social)](https://github.com/B2nd9R/cybersentinel)

<img src="assets/img/Banner.png" alt="CyberSentinel Banner" width="600" style="border-radius: 10px;">

### 🤖 بوت حماية متقدم لسيرفرات الديسكورد مع ميزات أمان وتعليم شاملة

[⬇️ تثبيت البوت](https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands) • [📚 التوثيق](docs/README.md) • [💬 سيرفر الدعم](https://discord.gg/your-invite)

</div>

---

## ✨ لماذا CyberSentinel؟

<div align="center">

| 🚀 سهل الاستخدام | 💪 قوي وموثوق | 🔄 تحديثات مستمرة |
|-----------------|---------------|-------------------|
| إعداد سريع في دقائق | حماية 24/7 | تحديثات أمنية أسبوعية |
| واجهة سهلة الاستخدام | تحليل ذكي للتهديدات | ميزات جديدة شهرياً |
| دعم فني متميز | أداء عالي | تحسينات مستمرة |

</div>

## 🌟 المميزات الرئيسية

<div align="center">

| 🛡️ الحماية | 📊 المراقبة | 🎓 التعليم |
|------------|------------|------------|
| ✨ حماية متقدمة ضد التهديدات | 📈 تحليل السلوك المشبوه | 📚 دروس في الأمان السيبراني |
| 🔍 فحص الروابط والملفات | 📊 تقارير وإحصائيات شاملة | 🎯 اختبارات تفاعلية |
| 🛑 منع الهجمات والسبام | 🕒 سجل أحداث متقدم | 💡 نصائح أمنية يومية |

</div>

## 🚀 البدء السريع

### 📋 المتطلبات الأساسية

<details>
<summary>انقر للعرض</summary>

- Python 3.8+
- Discord.py 2.0+
- حساب Discord للبوت
- مفتاح API من VirusTotal
- ذاكرة: 512MB كحد أدنى
- معالج: 1 vCPU كحد أدنى
</details>

## ⚙️ التثبيت

1. نسخ المستودع:
```bash
git clone https://github.com/yourusername/cybersentinel.git
cd cybersentinel
```

2. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

3. إعداد ملف .env :
```bash
DISCORD_TOKEN=your_token_here
OWNER_ID=your_id_here
VIRUSTOTAL_API_KEY=your_key_here
```

## 🚀 التشغيل
```bash
git clone https://github.com/B2nd9R/cybersentinel.git
cd cybersentinel
python main.py
```

# أوامر بوت الحماية الأمنية

## 🛠️ أوامر الإدارة والتحكم
| الأمر | الوصف | مثال |
|-------|-------|-------|
| `!setup` | إعداد البوت في السيرفر | `!setup` |
| `!set_admin_channel` | تحديد قناة الإدارة | `!set_admin_channel #قناة-الإدارة` |
| `!protection_level` | تحديد مستوى الحماية (1-4) | `!protection_level 3` |
| `!ban_threshold` | تحديد عتبة الحظر التلقائي | `!ban_threshold 15` |
| `!toggle_feature` | تفعيل/تعطيل ميزة | `!toggle_feature anti_raid` |
| `!security_status` | عرض حالة الأمان | `!security_status` |
| `!reset_user` | إعادة تعيين نقاط الخطر | `!reset_user @مستخدم` |
| `!view_threats` | عرض التهديدات الأخيرة | `!view_threats 5` |
| `!export_data` | تصدير بيانات الأمان | `!export_data` |

## 📊 أوامر التقارير والإحصائيات
| الأمر | الوصف | مثال |
|-------|-------|-------|
| `!security_report` | تقرير أمني شامل | `!security_report 30` |
| `!threat_log` | سجل التهديدات | `!threat_log @مستخدم 10` |
| `!stats` | إحصائيات أمنية سريعة | `!stats` |

## 🔒 أوامر الأمان والحماية
| الأمر | الوصف | مثال |
|-------|-------|-------|
| `!scan_url` | فحص الروابط | `!scan_url https://example.com` |
| `!user_info` | معلومات أمان المستخدم | `!user_info @مستخدم` |
| `!warn_user` | تحذير مستخدم | `!warn_user @مستخدم السبب` |
| `!security_scan` | فحص أمني شامل | `!security_scan` |
| `!lockdown` | قفل السيرفر مؤقتاً | `!lockdown 30` |
| `!clear_threats` | مسح سجل التهديدات | `!clear_threats @مستخدم` |
| `!quarantine` | عزل مستخدم مؤقتاً | `!quarantine @مستخدم 120` |

## ⚠️ متطلبات الصلاحيات
- معظم الأوامر تحتاج صلاحيات إدارية
- بعض الأوامر تحتاج:
  - `manage_guild`
  - `administrator`
  - `manage_roles`

## 📌 ملاحظات هامة
1. يمكن تغيير القيم الرقمية حسب الحاجة
2. الحد الأقصى للقيم:
   - أيام التقارير: 90 يوم
   - مدة القفل: 60 دقيقة
   - مدة العزل: 1440 دقيقة (24 ساعة)
3. جميع الأحداث مسجلة في سجلات الأمان

## 🔧 التخصيص
- مستويات الحماية : 4 مستويات قابلة للتخصيص
- عتبات التحذير : قابلة للتعديل حسب احتياجات السيرفر
- قنوات السجلات : يمكن تخصيص قنوات التنبيهات والسجلات
## ⚠️ متطلبات الصلاحيات
- معظم الأوامر تتطلب صلاحيات إدارية
- الصلاحيات المطلوبة:
  - ADMINISTRATOR
  - MANAGE_GUILD
  - MANAGE_ROLES
  - VIEW_AUDIT_LOG
  - MANAGE_MESSAGES
## 📌 ملاحظات هامة
- حدود القيم :
  
  - تقارير: حتى 90 يوم
  - قفل السيرفر: حتى 60 دقيقة
  - عزل المستخدمين: حتى 24 ساعة
- السجلات : جميع الأحداث يتم تسجيلها تلقائياً
- النسخ الاحتياطي : يتم عمل نسخة احتياطية يومياً
- التحديثات : يتم إصدار تحديثات أمنية بشكل دوري

## 📜 الترخيص
هذا المشروع مرخص تحت رخصة MIT

## 🤝 المساهمة
نرحب بمساهماتكم! يرجى قراءة دليل المساهمة للمزيد من المعلومات.

<div align="center">
⭐ لا تنسى إضافة نجمة للمشروع إذا أعجبك!
<a href="https://github.com/B2nd9R/cybersentinel/stargazers"><img src="https://img.shields.io/github/stars/B2nd9R/cybersentinel?style=social" alt="GitHub stars"></a>

صنع بـ ❤️ بواسطة B2nd9R

</div> 