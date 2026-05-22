/**
 * 用户自定义常量
 *
 * 简单值可通过环境变量配置（详见根目录 .env.example）：
 *   VITE_PLAYER_NAME   显示称呼
 *   VITE_PLAYER_IGN    游戏 ID
 *   VITE_RUNTIME_START 计时起始时间
 *
 * 复杂映射（副本名、排行榜名）直接改下面两个 Map 即可
 */

// ── 从环境变量读取（Vite 暴露 import.meta.env）────────────
const ENV = typeof import.meta !== "undefined" ? import.meta.env : {}

/** 玩家显示称呼 */
export const PLAYER_NAME = ENV.VITE_PLAYER_NAME || "卡死鱼"

/** 玩家游戏 ID */
export const PLAYER_IGN = ENV.VITE_PLAYER_IGN || "Kasyu_pwq"

/** 运行时统计起始时间 */
export const RUNTIME_START = ENV.VITE_RUNTIME_START || "2026-05-20T00:00:00"

// ── Raid / 公会 Raid 名称展示映射 ─────────────────────────
// 新增副本在这里加一行即可
export const RAID_NAME_MAP = {
  "The Canyon Colossus": "峡谷巨像 (The Canyon Colossus)",
  "Orphion's Nexus of Light": "奥菲恩之光枢纽 (Orphion's Nexus)",
  "The Nameless Anomaly": `${PLAYER_NAME}第二爱的tna (The Nameless Anomaly)`,
  "Nest of the Grootslangs": "打虫子 (Nest of the Grootslangs)",
  "The Wartorn Palace": `${PLAYER_NAME}最爱的黄宫 (The Wartorn Palace)`,
}

// ── 排行榜 / 技能等级字段展示映射 ─────────────────────────
// 新增排名项在这里加一行即可
export const RANKING_NAME_MAP = {
  combatSoloLevel: "战斗等级 (单人)",
  combatGlobalLevel: "战斗等级 (全局)",
  totalSoloLevel: "总等级 (单人)",
  totalGlobalLevel: "总等级 (全局)",
  professionsSoloLevel: "专业总等级 (单人)",
  professionsGlobalLevel: "专业总等级 (全局)",
  globalPlayerContent: "全局玩家内容排名",
  playerContent: "玩家内容分",
  frumaCompletion: "TWP",
  frumaSrPlayers: "TWP速通玩家排名",
  orphionCompletion: "NOL",
  orphionSrPlayers: "NOL速通玩家排名",
  colossusCompletion: "TCC",
  colossusSrPlayers: "TCC速通玩家排名",
  namelessCompletion: "TNA",
  namelessSrPlayers: "TNA速通玩家排名",
  grootslangCompletion: "NOTG",
  grootslangSrPlayers: "NOTG速通玩家排名",
  tailoringLevel: "裁缝等级",
  armouringLevel: "锻甲等级",
  jewelingLevel: "珠宝等级",
  miningLevel: "采矿等级",
  fishingLevel: "钓鱼等级",
  farmingLevel: "农耕等级",
  woodcuttingLevel: "伐木等级",
  cookingLevel: "烹饪等级",
  weaponsmithingLevel: "武器锻造等级",
  woodworkingLevel: "木工等级",
  alchemismLevel: "炼金等级",
  scribingLevel: "卷轴抄写等级",
  warsCompletion: "公会战完成度排名",
}
