# web/app.py

import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys

# --- إعداد المسارات الأساسية ---
WEB_DIR = Path(__file__).resolve().parent
BASE_DIR = WEB_DIR.parent

# --- إضافة جذر المشروع إلى مسار Python (إذا لزم الأمر لوحدات أخرى) ---
sys.path.insert(0, str(BASE_DIR))

# from config import Config # مثال: إذا كنت ستستخدم إعدادات من config.py

# --- تهيئة تطبيق FastAPI ---
app = FastAPI(
    title="CyberSentinel Web Dashboard",
    description="لوحة تحكم ويب لبوت CyberSentinel Discord.",
    version="1.0.0"
)

# --- إعداد مسارات المجلدات للملفات الثابتة والقوالب ---
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"

# --- تحميل الملفات الثابتة ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# --- إعداد قوالب Jinja2 ---
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- نظام مصادقة مبدئي (مثال) ---
# TODO: استبدل هذا بنظام مصادقة حقيقي وآمن!
DUMMY_USERS = {
    "admin": {"password": "supersecret"} # يجب أن تأتي هذه من إعدادات آمنة
}

# --- دوال مساعدة للمصادقة (مثال) ---
async def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token and session_token in DUMMY_USERS: # تحقق مبسط جدًا
        return session_token
    return None

# --- مسارات (Routes) تطبيق الويب ---

@app.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    """يعرض صفحة تسجيل الدخول."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=RedirectResponse, name="handle_login")
async def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """يعالج بيانات تسجيل الدخول."""
    # TODO: استخدام دالة hash آمنة لمقارنة كلمات المرور
    if username in DUMMY_USERS and DUMMY_USERS[username]["password"] == password:
        response = RedirectResponse(url=app.url_path_for("dashboard_page"), status_code=302)
        # TODO: استخدام نظام جلسات آمن
        response.set_cookie(key="session_token", value=username, httponly=True, samesite="Lax")
        return response
    return RedirectResponse(url=f"{app.url_path_for('login_page')}?error=1", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse, name="dashboard_page")
async def dashboard_page(request: Request, user: str = Depends(get_current_user)):
    """يعرض لوحة التحكم الرئيسية إذا كان المستخدم مسجلاً دخوله."""
    if not user:
        return RedirectResponse(url=app.url_path_for("login_page"), status_code=302)
    # TODO: إنشاء ملف dashboard.html فعلي
    return templates.TemplateResponse("dashboard_placeholder.html", {"request": request, "user": user})

@app.post("/logout", response_class=RedirectResponse, name="logout")
async def logout(request: Request):
    """يسجل خروج المستخدم."""
    response = RedirectResponse(url=app.url_path_for("login_page"), status_code=302)
    response.delete_cookie("session_token")
    return response

# --- نقطة تشغيل التطبيق (إذا تم تشغيل هذا الملف مباشرة) ---
if __name__ == "__main__":
    # TODO: قراءة HOST و PORT من إعدادات البوت (Config) أو متغيرات البيئة
    uvicorn.run(
        "app:app",
        host="127.0.0.1", # أو Config.WEB_HOST
        port=8000,        # أو Config.WEB_PORT
        reload=True,
        log_level="info"
    )
