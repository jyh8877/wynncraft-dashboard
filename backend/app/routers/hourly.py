from datetime import date

from fastapi import APIRouter, Query
from sqlmodel import Session, select

from ..database import engine
from ..models.summary import HourlySummary

router = APIRouter(tags=["hourly"])


@router.get("/api/hourly_records_by_date")
def get_hourly_records_by_date(target_date: date = Query(default_factory=date.today)):
    with Session(engine) as session:
        records = session.exec(
            select(HourlySummary)
            .where(HourlySummary.target_date == target_date)
            .order_by(HourlySummary.target_hour.asc())
        ).all()

        return {
            "date": str(target_date),
            "count": len(records),
            "data": records,
        }
