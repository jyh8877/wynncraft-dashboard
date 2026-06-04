"""FastAPI 入口 — 仅负责 lifespan、CORS、路由注册、调度器启动"""

import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import create_db_and_tables
from .services.fetcher import fetch_and_store_player_data
from .services.archiver import archive_and_clean_hourly_data, archive_daily_data_from_hourly
from .routers import (
    fetch_router,
    history_router,
    logs_router,
    summary_router,
    hourly_router,
)
from .config import FETCH_INTERVAL_MINUTES

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    scheduler = AsyncIOScheduler()

    scheduler.add_job(fetch_and_store_player_data, "interval", minutes=FETCH_INTERVAL_MINUTES)
    scheduler.add_job(archive_and_clean_hourly_data, "cron", minute=1)
    scheduler.add_job(archive_daily_data_from_hourly, "cron", hour=0, minute=5)

    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="Wynncraft Player Stats API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──────────────────────────────────────────────
app.include_router(fetch_router)
app.include_router(history_router)
app.include_router(logs_router)
app.include_router(summary_router)
app.include_router(hourly_router)
