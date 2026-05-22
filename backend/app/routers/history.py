from fastapi import APIRouter, Query
from sqlmodel import Session, select

from ..database import engine
from ..models.player import PlayerHistory

router = APIRouter(tags=["history"])


@router.get("/api/history")
def get_player_history(limit: int = 30):
    with Session(engine) as session:
        results = session.exec(
            select(PlayerHistory).order_by(PlayerHistory.record_time.desc()).limit(limit)
        ).all()
        return list(reversed(results))
