import contextlib
from datetime import datetime, date
from typing import Optional

import httpx
from fastapi import FastAPI, BackgroundTasks, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
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

# === 新增：事件日志表 ===
class PlayerEventLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    record_time: datetime = Field(default_factory=datetime.now)
    event_category: str = Field(index=True) # 分类：例如 "RAID", "LEVEL_UP", "STATS"
    message: str # 具体的日志内容

# 数据库连接
sqlite_url = "sqlite:///player_data.db"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# ==========================================
# 2. 核心抓取与对比差异 (Diff) 逻辑
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
            
            # 组装新记录
            new_record = PlayerHistory(
                is_online=data.get("online", False),
                server=data.get("server"),
                playtime=data.get("playtime", 0.0),
                total_level=global_data.get("totalLevel", 0),
                mobs_killed=global_data.get("mobsKilled", 0),
                chests_found=global_data.get("chestsFound", 0),
                raid_damage_dealt=raid_stats.get("damageDealt", 0),
                ranking_data=data.get("ranking", {}),
                raids_data=global_data.get("raids", {}).get("list", {}),
                guild_raids_data=global_data.get("guildRaids", {}).get("list", {})
            )
            
            with Session(engine) as session:
                # 1. 查出数据库里的最后一条记录（用于做差异对比）
                last_record = session.exec(select(PlayerHistory).order_by(PlayerHistory.record_time.desc()).limit(1)).first()
                
                logs_to_insert = []
                current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if last_record:
                    # --- 差异对比逻辑开始 ---
                    
                    # 检查 Raid 次数变化
                    for raid_name, new_count in new_record.raids_data.items():
                        old_count = last_record.raids_data.get(raid_name, 0)
                        if new_count > old_count:
                            logs_to_insert.append(PlayerEventLog(
                                event_category="RAID",
                                message=f"[{current_time_str}] 成功通关了 {new_count - old_count} 次 {raid_name} (当前总计: {new_count})"
                            ))

                    # 检查 Raid 死亡数变化
                    if new_record.raid_deaths > last_record.raid_deaths:
                        logs_to_insert.append(PlayerEventLog(
                            event_category="RAID_DEATH",
                            message=f"[{current_time_str}] Raid 死亡数增加了 {new_record.raid_deaths - last_record.raid_deaths} 次 (当前总计: {new_record.raid_deaths})"
                        ))
                            
                    # 检查总等级变化
                    if new_record.total_level > last_record.total_level:
                        logs_to_insert.append(PlayerEventLog(
                            event_category="LEVEL_UP",
                            message=f"[{current_time_str}] 总等级提升了 {new_record.total_level - last_record.total_level} 级！ (当前总等级: {new_record.total_level})"
                        ))
                    
                
                # 2. 将新记录和生成的日志一起保存
                session.add(new_record)
                for log_entry in logs_to_insert:
                    session.add(log_entry)
                    print(f"💡 触发新日志: {log_entry.message}")
                    
                session.commit()
                
            print(f"[{datetime.now()}] 数据同步完成。")
            
        except Exception as e:
            print(f"[{datetime.now()}] 抓取失败: {e}")

# ==========================================
# 3. 定时任务与 API 路由
# ==========================================
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    scheduler = AsyncIOScheduler()
    # === 修改：变更为每 5 分钟执行一次 ===
    scheduler.add_job(fetch_and_store_player_data, 'interval', minutes=5)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan, title="Wynncraft Player Stats API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 开发环境下允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api/history")
def get_player_history(limit: int = 30):
    with Session(engine) as session:
        results = session.exec(select(PlayerHistory).order_by(PlayerHistory.record_time.desc()).limit(limit)).all()
        return list(reversed(results))

# === 新增：获取变动日志 API ===
@app.get("/api/logs")
def get_event_logs(limit: int = 50, category: Optional[str] = None):
    """获取玩家的动态日志时间线"""
    with Session(engine) as session:
        query = select(PlayerEventLog)
        if category:
            query = query.where(PlayerEventLog.event_category == category)
        query = query.order_by(PlayerEventLog.record_time.desc()).limit(limit)
        return session.exec(query).all()

# === 新增：每日总结 API ===
@app.get("/api/daily_summary")
def get_daily_summary(target_date: date = Query(default_factory=date.today)):
    """传入指定的日期 (YYYY-MM-DD)，获取当天的各项数据增长量"""
    with Session(engine) as session:
        # 获取该日期当天的第一条和最后一条记录
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        statement = select(PlayerHistory).where(
            PlayerHistory.record_time >= start_of_day,
            PlayerHistory.record_time <= end_of_day
        ).order_by(PlayerHistory.record_time.asc())
        
        records = session.exec(statement).all()
        
        if not records or len(records) < 2:
            return {"message": "当日数据不足两条，无法生成总结比对。"}
            
        first_record = records[0]
        last_record = records[-1]
        
        # 计算差值
        summary = {
            "date": str(target_date),
            "playtime_gained": round(last_record.playtime - first_record.playtime, 2),
            "levels_gained": last_record.total_level - first_record.total_level,
            "mobs_killed_today": last_record.mobs_killed - first_record.mobs_killed,
            "chests_found_today": last_record.chests_found - first_record.chests_found,
            "damage_dealt_today": last_record.raid_damage_dealt - first_record.raid_damage_dealt,
            "raids_completed": {}
        }
        
        # 计算各项 Raid 的当日差值
        for raid, last_count in last_record.raids_data.items():
            first_count = first_record.raids_data.get(raid, 0)
            if last_count > first_count:
                summary["raids_completed"][raid] = last_count - first_count
                
        return summary

@app.post("/api/fetch_now")
async def trigger_fetch_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_store_player_data)
    return {"message": "已在后台触发抓取任务"}