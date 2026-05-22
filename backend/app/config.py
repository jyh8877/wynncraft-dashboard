"""应用配置 — 从环境变量读取，带默认值"""

import os

TARGET_PLAYER: str = os.getenv("TARGET_PLAYER", "Kasyu_pwq")
PLAYER_NAME: str = os.getenv("PLAYER_NAME", "卡死鱼")
API_URL: str = f"https://api.wynncraft.com/v3/player/{TARGET_PLAYER}"
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///player_data.db")
FETCH_INTERVAL_MINUTES: int = int(os.getenv("FETCH_INTERVAL_MINUTES", "5"))
