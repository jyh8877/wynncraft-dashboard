"""定时数据抓取与 Diff 逻辑"""

from datetime import datetime, timedelta

import httpx
from sqlmodel import Session, select

from ..config import TARGET_PLAYER, API_URL, FETCH_INTERVAL_MINUTES
from ..constants import PLAYER_NAME
from ..database import engine
from ..models.player import PlayerHistory
from ..models.event import PlayerEventLog


async def fetch_and_store_player_data():
    """从 Wynncraft API 抓取玩家数据，存入 PlayerHistory 并生成事件日志"""
    print(f"[{datetime.now()}] 正在抓取玩家数据...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_URL, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            global_data = data.get("globalData") or {}
            raid_stats = global_data.get("raidStats") or {}

            new_record = PlayerHistory(
                is_online=data.get("online", False),
                server=data.get("server"),
                playtime=data.get("playtime", 0.0),
                total_level=global_data.get("totalLevel", 0),
                mobs_killed=global_data.get("mobsKilled", 0),
                chests_found=global_data.get("chestsFound", 0),

                completed_quests=global_data.get("completedQuests", 0),
                world_events=global_data.get("worldEvents", 0),
                content_completion=global_data.get("contentCompletion", 0),
                wars=global_data.get("wars", 0),

                raid_damage_dealt=raid_stats.get("damageDealt", 0),
                raid_damage_taken=raid_stats.get("damageTaken", 0),
                raid_health_healed=raid_stats.get("healthHealed", 0),
                raid_deaths=raid_stats.get("deaths", 0),

                ranking_data=data.get("ranking", {}),
                raids_data=global_data.get("raids", {}).get("list", {}),
                guild_raids_data=global_data.get("guildRaids", {}).get("list", {}),
            )

            with Session(engine) as session:
                # 只取最近 FETCH_INTERVAL_MINUTES*3 分钟内的快照作为比较基准，防止与过期记录对比
                cutoff_time = datetime.now() - timedelta(minutes=FETCH_INTERVAL_MINUTES * 3)
                last_record = session.exec(
                    select(PlayerHistory)
                    .where(PlayerHistory.record_time >= cutoff_time)
                    .order_by(PlayerHistory.record_time.desc())
                    .limit(1)
                ).first()
                logs_to_insert = []

                if last_record:
                    # ── 在线状态变化（上线 / 下线） ────────────────
                    if new_record.is_online and not last_record.is_online:
                        logs_to_insert.append(PlayerEventLog(
                            event_category="ONLINE",
                            message=f"{PLAYER_NAME}上线了！服务器: {new_record.server or '未知'}",
                        ))
                    elif not new_record.is_online and last_record.is_online:
                        logs_to_insert.append(PlayerEventLog(
                            event_category="OFFLINE",
                            message=f"{PLAYER_NAME}从 {last_record.server or '未知'} 下线了",
                        ))
                    # ── 切服 ──────────────────────────────────────
                    elif (new_record.is_online and last_record.is_online
                          and new_record.server and last_record.server
                          and new_record.server != last_record.server):
                        logs_to_insert.append(PlayerEventLog(
                            event_category="SERVER_SWITCH",
                            message=f"{PLAYER_NAME}从 {last_record.server} 转场到了 {new_record.server}",
                        ))

                    for raid_name, new_count in new_record.raids_data.items():
                        old_count = last_record.raids_data.get(raid_name, 0)
                        if new_count > old_count:
                            logs_to_insert.append(PlayerEventLog(
                                event_category="RAID",
                                message=f"成功通关了 {new_count - old_count} 次 {raid_name}",
                            ))
                    for raid_name, new_count in new_record.guild_raids_data.items():
                        old_count = last_record.guild_raids_data.get(raid_name, 0)
                        if new_count > old_count:
                            logs_to_insert.append(PlayerEventLog(
                                event_category="GUILD_RAID",
                                message=f"成功通关了 {new_count - old_count} 次 g {raid_name}",
                            ))
                    # if new_record.ranking_data != last_record.ranking_data:
                    #     logs_to_insert.append(PlayerEventLog(
                    #         event_category="RANKING",
                    #         message="排行榜数据已更新。",
                    #     ))
                    if new_record.total_level > last_record.total_level:
                        logs_to_insert.append(PlayerEventLog(
                            event_category="LEVEL_UP",
                            message=f"总等级提升了 {new_record.total_level - last_record.total_level} 级！",
                        ))

                session.add(new_record)
                for log_entry in logs_to_insert:
                    session.add(log_entry)
                session.commit()

            print(f"[{datetime.now()}] 数据同步完成。")
        except Exception as e:
            print(f"[{datetime.now()}] 抓取失败: {e}")



