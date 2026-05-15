"""Camera Tracking AI — Backend API Entry Point."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from sqlalchemy import select

from config import get_settings
from database import init_db, close_db, async_session
from models.user import User
from services.ws_manager import ws_manager

from routers import auth, cameras, ai_ingest, ai_adapter, history

CROPS_DIR = Path(os.getenv("CROPS_DIR", "/app/cropped_data"))
CROPS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_default_users():
    """Create default admin and operator users if they don't exist."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == settings.admin_username))
        if not result.scalar_one_or_none():
            admin = User(
                username=settings.admin_username,
                password_hash=pwd_context.hash(settings.admin_password),
                role="admin",
            )
            db.add(admin)
            logger.info(f"Created default admin user: {settings.admin_username}")

        result = await db.execute(select(User).where(User.username == "operator"))
        if not result.scalar_one_or_none():
            operator = User(
                username="operator",
                password_hash=pwd_context.hash("Operator@2026!"),
                role="operator",
            )
            db.add(operator)
            logger.info("Created default operator user")

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Starting Camera Tracking AI Backend...")
    await init_db()
    await seed_default_users()
    logger.info("Backend ready.")
    yield
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title="Camera Tracking AI — Backend",
    description="Camera management, streaming, and AI detection results API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend and go2rtc
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(ai_ingest.router)    # /api/ai/* (new format — priority)
app.include_router(ai_adapter.router)   # /api/persons, /api/vehicles, /api/alerts (legacy format)
app.include_router(history.router)      # Note: history uses GET, adapter uses POST — no conflict

# Serve crop images as static files
app.mount("/api/crops", StaticFiles(directory=str(CROPS_DIR)), name="crops")


# WebSocket endpoint for dashboard real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Clients can send ping/pong or request data
            if data == "ping":
                await ws_manager.send_personal(websocket, "pong", {})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "camera-tracking-backend"}
