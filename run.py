import asyncio
import logging
from main import main as run_discord_bot
from web.app import app as fastapi_app

import uvicorn

logger = logging.getLogger(__name__)

async def start_fastapi():
    """تشغيل خادم FastAPI داخل حلقة asyncio."""
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def run_all():
    """تشغيل البوت وFastAPI في وقت واحد."""
    await asyncio.gather(
        run_discord_bot(),
        start_fastapi()
    )

if __name__ == "__main__":
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        logger.info("تم إيقاف التطبيق يدويًا.")
