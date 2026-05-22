from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PlayerEventLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    record_time: datetime = Field(default_factory=datetime.now)
    event_category: str = Field(index=True)
    message: str
