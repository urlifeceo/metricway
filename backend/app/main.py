from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.alerts import send_daily_reports
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.auth import router as auth_router
from app.core.auth import get_current_user

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        send_daily_reports,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_alert_job",
        replace_existing=True
    )
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="TgMetrics Dashboard API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    projects_router,
    prefix="/api/v1",
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
