import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import api, ws
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="GlanceOS", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.include_router(ws.router)

# Serve built frontend assets in production so kiosk mode can load from the backend directly.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    logging.getLogger("glanceos.main").info("Serving frontend from %s", frontend_dist)
else:
    logging.getLogger("glanceos.main").info(
        "Frontend dist not found at %s; static UI serving disabled", frontend_dist
    )
