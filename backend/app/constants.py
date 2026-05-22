"""用户自定义常量 — 简单值已在 .env / .env.example 中配置"""

from .config import PLAYER_NAME

# ── Raid 名称展示映射 ─────────────────────────────────────
# 新增副本在这里加一行即可，格式： "API返回的英文名": "你想显示的中文名",
RAID_NAME_MAP: dict[str, str] = {
    "The Canyon Colossus": "峡谷巨像 (The Canyon Colossus)",
    "Orphion's Nexus of Light": "奥菲恩之光枢纽 (Orphion's Nexus)",
    "The Nameless Anomaly": f"{PLAYER_NAME}第二爱的tna (The Nameless Anomaly)",
    "Nest of the Grootslangs": "打虫子 (Nest of the Grootslangs)",
    "The Wartorn Palace": f"{PLAYER_NAME}最爱的黄宫 (The Wartorn Palace)",
}
