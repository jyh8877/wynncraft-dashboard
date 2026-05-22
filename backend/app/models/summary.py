from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON, BigInteger


class HourlySummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_date: date = Field(index=True)
    target_hour: int = Field(index=True)

    playtime_gained: float = Field(default=0.0)
    levels_gained: int = Field(default=0)
    mobs_killed_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    chests_found_this_hour: int = Field(default=0)

    completed_quests_this_hour: int = Field(default=0)
    world_events_this_hour: int = Field(default=0)
    content_completion_this_hour: int = Field(default=0)
    wars_this_hour: int = Field(default=0)

    damage_dealt_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    damage_taken_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    health_healed_this_hour: int = Field(default=0, sa_column=Column(BigInteger))
    deaths_this_hour: int = Field(default=0)

    raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    guild_raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ranking_data: dict = Field(default_factory=dict, sa_column=Column(JSON))


class DailySummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_date: date = Field(unique=True, index=True)

    playtime_gained: float = Field(default=0.0)
    levels_gained: int = Field(default=0)
    mobs_killed_today: int = Field(default=0, sa_column=Column(BigInteger))
    chests_found_today: int = Field(default=0)

    completed_quests_today: int = Field(default=0)
    world_events_today: int = Field(default=0)
    content_completion_today: int = Field(default=0)
    wars_today: int = Field(default=0)

    damage_dealt_today: int = Field(default=0, sa_column=Column(BigInteger))
    damage_taken_today: int = Field(default=0, sa_column=Column(BigInteger))
    health_healed_today: int = Field(default=0, sa_column=Column(BigInteger))
    deaths_today: int = Field(default=0)

    raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    guild_raids_completed: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ranking_data: dict = Field(default_factory=dict, sa_column=Column(JSON))
