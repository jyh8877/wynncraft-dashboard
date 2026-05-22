from typing import Optional

from fastapi import APIRouter
from sqlmodel import Session, select

from ..database import engine
from ..models.event import PlayerEventLog

router = APIRouter(tags=["logs"])


@router.get("/api/logs")
def get_event_logs(limit: int = 50, category: Optional[str] = None):
    with Session(engine) as session:
        query = select(PlayerEventLog)
        if category:
            query = query.where(PlayerEventLog.event_category == category)
        query = query.order_by(PlayerEventLog.record_time.desc()).limit(limit)
        return session.exec(query).all()
