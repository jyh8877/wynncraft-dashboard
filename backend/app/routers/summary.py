from datetime import date

from fastapi import APIRouter, Query
from sqlmodel import Session, select

from ..database import engine
from ..models.summary import DailySummary, HourlySummary

router = APIRouter(tags=["summary"])


@router.get("/api/daily_summary")
def get_daily_summary(target_date: date = Query(default_factory=date.today)):
    with Session(engine) as session:
        saved = session.exec(
            select(DailySummary).where(DailySummary.target_date == target_date)
        ).first()
        if saved:
            return saved

        hourly_records = session.exec(
            select(HourlySummary).where(HourlySummary.target_date == target_date)
        ).all()
        if not hourly_records:
            return {"message": "当前暂无该日期的小时级统计数据。"}

        summary = {
            "target_date": str(target_date),
            "playtime_gained": round(sum(h.playtime_gained for h in hourly_records), 2),
            "levels_gained": sum(h.levels_gained for h in hourly_records),
            "mobs_killed_today": sum(h.mobs_killed_this_hour for h in hourly_records),
            "chests_found_today": sum(h.chests_found_this_hour for h in hourly_records),

            "completed_quests_today": sum(h.completed_quests_this_hour for h in hourly_records),
            "world_events_today": sum(h.world_events_this_hour for h in hourly_records),
            "content_completion_today": sum(h.content_completion_this_hour for h in hourly_records),
            "wars_today": sum(h.wars_this_hour for h in hourly_records),

            "damage_dealt_today": sum(h.damage_dealt_this_hour for h in hourly_records),
            "damage_taken_today": sum(h.damage_taken_this_hour for h in hourly_records),
            "health_healed_today": sum(h.health_healed_this_hour for h in hourly_records),
            "deaths_today": sum(h.deaths_this_hour for h in hourly_records),

            "raids_completed": {},
            "guild_raids_completed": {},
            "ranking_data": hourly_records[-1].ranking_data or {},
        }
        for h in hourly_records:
            for raid, count in h.raids_completed.items():
                summary["raids_completed"][raid] = summary["raids_completed"].get(raid, 0) + count
            for raid, count in h.guild_raids_completed.items():
                summary["guild_raids_completed"][raid] = (
                    summary["guild_raids_completed"].get(raid, 0) + count
                )
        return summary
