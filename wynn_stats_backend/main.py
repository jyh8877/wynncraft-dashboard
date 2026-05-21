import contextlib
from datetime import datetime, date, timedelta
from typing import Optional

import httpx
from fastapi import FastAPI, BackgroundTasks, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, delete
from sqlalchemy import Column, JSON, BigInteger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# 1. 数据库模型定义
# ==========================================
class PlayerHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    record_time: datetime = Field(default_factory=datetime.now)
    
    # 基础状态与游玩时间
    is_online: bool = Field(default=False)
    server: Optional[str] = Field(default=None)
    last_join: Optional[datetime] = Field(default=None)
    playtime: float = Field(default=0.0)
    
    # 公会动态
    guild_prefix: Optional[str] = Field(default=None)
    
    # 核心里程碑数据
    total_level: int = Field(default=0)
    mobs_killed: int = Field(default=0, sa_column=Column(BigInteger))
    chests_found: int = Field(default=0)
    completed_quests: int = Field(default=0)
    world_events: int = Field(default=0)
    content_completion: int = Field(default=0)
    wars: int = Field(default=0)
    
    # Raid 战斗统计数据
    raid_damage_dealt: int = Field(default=0, sa_column=Column(BigInteger))
    raid_damage_taken: int = Field(default=0, sa_column=Column(BigInteger))
    raid_health_healed: int = Field(default=0, sa_column=Column(BigInteger))
    raid_deaths: int = Field(default=0)
    
    # 复杂的列表类数据
    ranking_data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    raids_data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    guild_raids_data: dict = Field(default_factory=dict, sa_column=Column(JSON))


# === 新增：每小时总结持久化表 ===
class HourlySummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_date: date = Field(index=True)                  # 日期：2026-05-21
    target_hour: int = Field(index=True)                  # 小时：0-23
    
    playtime_gained: float = Field(default=0.0)
    levels_gained: int = Field(default=0)
    mobs_killed_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    chests_found_this_hour: int = Field(default=0)
    
    # 新增对齐：核心里程碑数据
    completed_quests_this_hour: int = Field(default=0)
    world_events_this_hour: int = Field(default=0)
    content_completion_this_hour: int = Field(default=0)
    wars_this_hour: int = Field(default=0)
    
    # 新增对齐：Raid 战斗统计
    damage_dealt_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    damage_taken_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    health_healed_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    deaths_this_hour: int = Field(default=0)
    
    raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    guild_raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ranking_data: dict = Field(default_factory=dict, sa_column=Column(JSON))

class DailySummary(SQLModel, table=True):
    """每日总结持久化表：由 24 个小时总结累加而来"""
    id: Optional[int] = Field(default=None, primary_key=True)
    target_date: date = Field(unique=True, index=True)
    
    playtime_gained: float = Field(default=0.0)
    levels_gained: int = Field(default=0)
    mobs_killed_today: int = Field(default=0, sa_column=Column(BigInteger))
    chests_found_today: int = Field(default=0)
    
    # 新增对齐：核心里程碑数据
    completed_quests_today: int = Field(default=0)
    world_events_today: int = Field(default=0)
    content_completion_today: int = Field(default=0)
    wars_today: int = Field(default=0)
    
    # 新增对齐：Raid 战斗统计
    damage_dealt_today: int = Field(default=0, sa_column=Column(BigInteger))
    damage_taken_today: int = Field(default=0, sa_column=Column(BigInteger))
    health_healed_today: int = Field(default=0, sa_column=Column(BigInteger))
    deaths_today: int = Field(default=0)
    
    raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    guild_raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ranking_data: dict = Field(default_factory=dict, sa_column=Column(JSON))

class PlayerEventLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    record_time: datetime = Field(default_factory=datetime.now)
    event_category: str = Field(index=True) 
    message: str 


sqlite_url = "sqlite:///player_data.db"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# ==========================================
# 2. 定时数据抓取与 Diff 逻辑
# ==========================================
TARGET_PLAYER = "Kasyu_pwq"
API_URL = f"https://api.wynncraft.com/v3/player/{TARGET_PLAYER}"

async def fetch_and_store_player_data():
    print(f"[{datetime.now()}] 正在抓取玩家数据...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_URL, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            global_data = data.get("globalData") or {}
            raid_stats = global_data.get("raidStats") or {}
            
            # 【修复】在这里补全解析 API 数据，与 PlayerHistory 字段完全对齐
            new_record = PlayerHistory(
                is_online=data.get("online", False),
                server=data.get("server"),
                playtime=data.get("playtime", 0.0),
                total_level=global_data.get("totalLevel", 0),
                mobs_killed=global_data.get("mobsKilled", 0),
                chests_found=global_data.get("chestsFound", 0),
                
                # 新增核心数据解析
                completed_quests=global_data.get("completedQuests", 0),
                world_events=global_data.get("worldEvents", 0),
                content_completion=global_data.get("contentCompletion", 0),
                wars=global_data.get("wars", 0),
                
                # 新增 Raid 数据解析
                raid_damage_dealt=raid_stats.get("damageDealt", 0),
                raid_damage_taken=raid_stats.get("damageTaken", 0),
                raid_health_healed=raid_stats.get("healthHealed", 0),
                raid_deaths=raid_stats.get("deaths", 0),
                
                # 新增排行榜数据解析
                # ranking_data=global_data.get("ranking", {}),
                ranking_data=data.get("ranking", {}),
                raids_data=global_data.get("raids", {}).get("list", {}),
                guild_raids_data=global_data.get("guildRaids", {}).get("list", {})
            )
            
            with Session(engine) as session:
                last_record = session.exec(select(PlayerHistory).order_by(PlayerHistory.record_time.desc()).limit(1)).first()
                logs_to_insert = []
                current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if last_record:
                    for raid_name, new_count in new_record.raids_data.items():
                        old_count = last_record.raids_data.get(raid_name, 0)
                        if new_count > old_count:
                            logs_to_insert.append(PlayerEventLog(
                                event_category="RAID",
                                message=f"[{current_time_str}] 成功通关了 {new_count - old_count} 次 {raid_name}"
                            ))
                    for raid_name, new_count in new_record.guild_raids_data.items():
                        old_count = last_record.guild_raids_data.get(raid_name, 0)
                        if new_count > old_count:
                            logs_to_insert.append(PlayerEventLog(
                                event_category="GUILD_RAID",
                                message=f"[{current_time_str}] 公会通关了 {new_count - old_count} 次 {raid_name}"
                            ))
                    if new_record.ranking_data != last_record.ranking_data:
                        logs_to_insert.append(PlayerEventLog(
                            event_category="RANKING",
                            message=f"[{current_time_str}] 排行榜数据已更新。"
                        ))
                    if new_record.total_level > last_record.total_level:
                        logs_to_insert.append(PlayerEventLog(
                            event_category="LEVEL_UP",
                            message=f"[{current_time_str}] 总等级提升了 {new_record.total_level - last_record.total_level} 级！"
                        ))
                
                session.add(new_record)
                for log_entry in logs_to_insert:
                    session.add(log_entry)
                session.commit()
            print(f"[{datetime.now()}] 数据同步完成。")
        except Exception as e:
            print(f"[{datetime.now()}] 抓取失败: {e}")


# ==========================================
# 3. 新增/重构的归档与清理逻辑
# ==========================================

def archive_and_clean_hourly_data():
    """每小时运行：结算【上一个小时】的数据，存入 HourlySummary，并清空该小时的快照"""
    now = datetime.now()
    last_hour_time = now - timedelta(hours=1)
    target_date = last_hour_time.date()
    target_hour = last_hour_time.hour
    
    start_of_hour = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=target_hour)
    end_of_hour = start_of_hour + timedelta(minutes=59, seconds=59)
    
    print(f"[{now}] 开始执行每小时总结，目标时段: {target_date} {target_hour}:00 ~ {target_hour}:59")
    
    with Session(engine) as session:
        existing = session.exec(select(HourlySummary).where(
            HourlySummary.target_date == target_date,
            HourlySummary.target_hour == target_hour
        )).first()
        if existing:
            return

        records = session.exec(
            select(PlayerHistory)
            .where(PlayerHistory.record_time >= start_of_hour, PlayerHistory.record_time <= end_of_hour)
            .order_by(PlayerHistory.record_time.asc())
        ).all()
        
        if not records:
            print(f"[{now}] 该时段无快照数据，跳过。")
            return
            
        first_rec = records[0]
        last_rec = records[-1]

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
            ranking_data=last_rec.ranking_data or {}
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
            session.exec(delete(PlayerHistory).where(
                PlayerHistory.record_time >= start_of_hour,
                PlayerHistory.record_time <= end_of_hour
            ))
            session.commit()
            print(f"[{now}] 成功归档 {target_hour} 点的每小时总结，并清空原始快照。")
        except Exception as e:
            session.rollback()
            print(f"[{now}] 每小时归档失败: {e}")


def archive_daily_data_from_hourly():
    """每天凌晨运行：将【昨天】的 24 条 HourlySummary 累加，存入 DailySummary"""
    yesterday = date.today() - timedelta(days=1)
    print(f"[{datetime.now()}] 开始生成每日总结（基于小时数据合并），目标日期: {yesterday}")
    
    with Session(engine) as session:
        existing = session.exec(select(DailySummary).where(DailySummary.target_date == yesterday)).first()
        if existing:
            return

        hourly_records = session.exec(
            select(HourlySummary).where(HourlySummary.target_date == yesterday)
        ).all()
        
        if not hourly_records:
            print(f"[{datetime.now()}] 未找到昨日的小时总结，无法合并生成每日总结。")
            return
            
        # 【修复】在这里对所有拓展出的字段进行求和累加
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
            ranking_data=hourly_records[-1].ranking_data or {}
        )
        
        for h in hourly_records:
            for raid, count in h.raids_completed.items():
                daily_summary.raids_completed[raid] = daily_summary.raids_completed.get(raid, 0) + count
            for raid, count in h.guild_raids_completed.items():
                daily_summary.guild_raids_completed[raid] = daily_summary.guild_raids_completed.get(raid, 0) + count
                
        try:
            session.add(daily_summary)
            session.commit()
            print(f"[{datetime.now()}] 成功生成并持久化 {yesterday} 的每日总结！")
        except Exception as e:
            session.rollback()
            print(f"[{datetime.now()}] 每日总结合并失败: {e}")


# ==========================================
# 4. 定时任务注册与 API 路由
# ==========================================
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(fetch_and_store_player_data, 'interval', minutes=5)
    scheduler.add_job(archive_and_clean_hourly_data, 'cron', minute=1)
    scheduler.add_job(archive_daily_data_from_hourly, 'cron', hour=0, minute=5)
    
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan, title="Wynncraft Player Stats API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/fetch_now")
async def trigger_fetch_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_store_player_data)
    return {"message": "已在后台触发抓取任务"}

@app.get("/api/history")
def get_player_history(limit: int = 30):
    with Session(engine) as session:
        results = session.exec(select(PlayerHistory).order_by(PlayerHistory.record_time.desc()).limit(limit)).all()
        return list(reversed(results))

@app.get("/api/logs")
def get_event_logs(limit: int = 50, category: Optional[str] = None):
    with Session(engine) as session:
        query = select(PlayerEventLog)
        if category:
            query = query.where(PlayerEventLog.event_category == category)
        query = query.order_by(PlayerEventLog.record_time.desc()).limit(limit)
        return session.exec(query).all()

@app.get("/api/daily_summary")
def get_daily_summary(target_date: date = Query(default_factory=date.today)):
    with Session(engine) as session:
        saved = session.exec(select(DailySummary).where(DailySummary.target_date == target_date)).first()
        if saved:
            return saved
            
        hourly_records = session.exec(select(HourlySummary).where(HourlySummary.target_date == target_date)).all()
        if not hourly_records:
            return {"message": "当前暂无该日期的小时级统计数据。"}
            
        # 【修复】在这里对齐动态查询的字典返回内容
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
            "ranking_data": hourly_records[-1].ranking_data or {}
        }
        for h in hourly_records:
            for raid, count in h.raids_completed.items():
                summary["raids_completed"][raid] = summary["raids_completed"].get(raid, 0) + count
            for raid, count in h.guild_raids_completed.items():
                summary["guild_raids_completed"][raid] = summary["guild_raids_completed"].get(raid, 0) + count
        return summary


@app.get("/api/hourly_records_by_date")
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
            "data": records
        }