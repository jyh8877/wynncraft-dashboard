from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON, BigInteger


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
