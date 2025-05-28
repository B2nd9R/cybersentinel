from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

app = FastAPI(
    title="CyberSentinel Dashboard",
    description="لوحة تحكم بوت الحماية الأمنية",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

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

# نقطة نهاية فحص الصحة
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# نقطة نهاية معلومات التطبيق
@app.get("/info")
async def get_info():
    return {
        "name": "CyberSentinel Dashboard",
        "version": "1.2.0",
        "status": "running"
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080)