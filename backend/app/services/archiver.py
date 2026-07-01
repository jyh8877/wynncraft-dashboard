"""归档与清理逻辑 — 小时归档 / 日归档"""

from datetime import datetime, date, timedelta

from sqlmodel import Session, select, delete

from ..database import engine
from ..models.player import PlayerHistory
from ..models.summary import HourlySummary, DailySummary


# ── 辅助 ──────────────────────────────────────────────────


def _first_and_last(records):
    return records[0], records[-1]


# ── 小时归档 ──────────────────────────────────────────────


def archive_and_clean_hourly_data():
    """每小时运行：结算【上一个小时】的数据，存入 HourlySummary，并清空该小时的快照"""
    now = datetime.now()
    last_hour_time = now - timedelta(hours=1)
    target_date = last_hour_time.date()
    target_hour = last_hour_time.hour

    start_of_hour = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=target_hour)
    end_of_hour = start_of_hour + timedelta(hours=1)  # exclusive upper bound

    print(f"[{now}] 开始执行每小时总结，目标时段: {target_date} {target_hour}:00 ~ {target_hour}:59")

    with Session(engine) as session:
        existing = session.exec(
            select(HourlySummary).where(
                HourlySummary.target_date == target_date,
                HourlySummary.target_hour == target_hour,
            )
        ).first()
        if existing:
            return

        records = session.exec(
            select(PlayerHistory)
            .where(PlayerHistory.record_time >= start_of_hour, PlayerHistory.record_time < end_of_hour)
            .order_by(PlayerHistory.record_time.asc())
        ).all()

        if not records:
            print(f"[{now}] 该时段无快照数据，跳过。")
            return

        first_rec, last_rec = _first_and_last(records)

        hourly_sub = HourlySummary(
            target_date=target_date,
            target_hour=target_hour,
            playtime_gained=round(last_rec.playtime - first_rec.playtime, 2),
            levels_gained=last_rec.total_level - first_rec.total_level,
            mobs_killed_this_hour=last_rec.mobs_killed - first_rec.mobs_killed,
            chests_found_this_hour=last_rec.chests_found - first_rec.chests_found,

            completed_quests_this_hour=last_rec.completed_quests - first_rec.completed_quests,
            world_events_this_hour=last_rec.world_events - first_rec.world_events,
            content_completion_this_hour=last_rec.content_completion - first_rec.content_completion,
            wars_this_hour=last_rec.wars - first_rec.wars,

            damage_dealt_this_hour=last_rec.raid_damage_dealt - first_rec.raid_damage_dealt,
            damage_taken_this_hour=last_rec.raid_damage_taken - first_rec.raid_damage_taken,
            health_healed_this_hour=last_rec.raid_health_healed - first_rec.raid_health_healed,
            deaths_this_hour=last_rec.raid_deaths - first_rec.raid_deaths,

            raids_completed={},
            guild_raids_completed={},
            ranking_data=last_rec.ranking_data or {},
        )

        for raid, last_count in last_rec.raids_data.items():
            first_count = first_rec.raids_data.get(raid, 0)
            if last_count > first_count:
                hourly_sub.raids_completed[raid] = last_count - first_count
        for raid, last_count in last_rec.guild_raids_data.items():
            first_count = first_rec.guild_raids_data.get(raid, 0)
            if last_count > first_count:
                hourly_sub.guild_raids_completed[raid] = last_count - first_count

        try:
            session.add(hourly_sub)
            # 删除当前小时之前的所有旧快照（防止僵尸记录累积）
            current_hour_start = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=now.hour)
            session.exec(
                delete(PlayerHistory).where(PlayerHistory.record_time < current_hour_start)
            )
            session.commit()
            print(f"[{now}] 成功归档 {target_hour} 点的每小时总结，并清空原始快照。")
        except Exception as e:
            session.rollback()
            print(f"[{now}] 每小时归档失败: {e}")


# ── 日归档 ────────────────────────────────────────────────


def archive_daily_data_from_hourly():
    """每天凌晨运行：将【昨天】的 24 条 HourlySummary 累加，存入 DailySummary"""
    yesterday = date.today() - timedelta(days=1)
    print(f"[{datetime.now()}] 开始生成每日总结（基于小时数据合并），目标日期: {yesterday}")

    with Session(engine) as session:
        existing = session.exec(
            select(DailySummary).where(DailySummary.target_date == yesterday)
        ).first()
        if existing:
            return

        hourly_records = session.exec(
            select(HourlySummary).where(HourlySummary.target_date == yesterday)
        ).all()

        if not hourly_records:
            print(f"[{datetime.now()}] 未找到昨日的小时总结，无法合并生成每日总结。")
            return

        daily_summary = DailySummary(
            target_date=yesterday,
            playtime_gained=round(sum(h.playtime_gained for h in hourly_records), 2),
            levels_gained=sum(h.levels_gained for h in hourly_records),
            mobs_killed_today=sum(h.mobs_killed_this_hour for h in hourly_records),
            chests_found_today=sum(h.chests_found_this_hour for h in hourly_records),

            completed_quests_today=sum(h.completed_quests_this_hour for h in hourly_records),
            world_events_today=sum(h.world_events_this_hour for h in hourly_records),
            content_completion_today=sum(h.content_completion_this_hour for h in hourly_records),
            wars_today=sum(h.wars_this_hour for h in hourly_records),

            damage_dealt_today=sum(h.damage_dealt_this_hour for h in hourly_records),
            damage_taken_today=sum(h.damage_taken_this_hour for h in hourly_records),
            health_healed_today=sum(h.health_healed_this_hour for h in hourly_records),
            deaths_today=sum(h.deaths_this_hour for h in hourly_records),

            raids_completed={},
            guild_raids_completed={},
            ranking_data=hourly_records[-1].ranking_data or {},
        )

        for h in hourly_records:
            for raid, count in h.raids_completed.items():
                daily_summary.raids_completed[raid] = (
                    daily_summary.raids_completed.get(raid, 0) + count
                )
            for raid, count in h.guild_raids_completed.items():
                daily_summary.guild_raids_completed[raid] = (
                    daily_summary.guild_raids_completed.get(raid, 0) + count
                )

        try:
            session.add(daily_summary)
            session.commit()
            print(f"[{datetime.now()}] 成功生成并持久化 {yesterday} 的每日总结！")
        except Exception as e:
            session.rollback()
            print(f"[{datetime.now()}] 每日总结合并失败: {e}")
