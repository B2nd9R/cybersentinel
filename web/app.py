from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Optional, List
import uvicorn
import jwt
import os

app = FastAPI(
    title="CyberSentinel Dashboard",
    description="لوحة تحكم بوت الحماية الأمنية",
    version="1.0.0"
)

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# الحصول على المسار المطلق للمجلد الثابت
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# تثبيت الملفات الثابتة
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# المسارات
@app.get("/")
async def read_root():
    return {"message": "مرحباً بك في واجهة برمجة تطبيقات CyberSentinel!"}

@app.get("/stats")
async def get_stats():
    return {
        "servers": 100,
        "users": 5000,
        "threats_blocked": 1500,
        "scans_performed": 10000
    }

@app.get("/recent-threats")
async def get_recent_threats():
    return [
        {
            "id": 1,
            "type": "رابط مشبوه",
            "severity": "عالي",
            "timestamp": "2024-01-20T12:00:00Z"
        },
        {
            "id": 2,
            "type": "محاولة اختراق",
            "severity": "متوسط",
            "timestamp": "2024-01-20T11:30:00Z"
        }
    ]

@app.get("/protection-status")
async def get_protection_status():
    return {
        "status": "نشط",
        "level": "متقدم",
        "last_update": "2024-01-20T12:00:00Z",
        "features_enabled": [
            "حماية الروابط",
            "منع الاختراق",
            "فحص الملفات"
        ]
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)