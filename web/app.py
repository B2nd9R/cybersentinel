from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from datetime import datetime
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

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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