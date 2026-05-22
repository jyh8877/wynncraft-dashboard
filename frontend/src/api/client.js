/**
 * API 客户端 — 统一封装所有后端 fetch 调用
 */

const BASE = "/api"

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

/** 获取最新 N 条高频快照 */
export function fetchHistory(limit = 30) {
  return get(`/history?limit=${limit}`)
}

/** 获取事件日志 */
export function fetchLogs(limit = 15, category = null) {
  const params = new URLSearchParams({ limit })
  if (category) params.set("category", category)
  return get(`/logs?${params}`)
}

/** 获取指定日期的每日总结 */
export function fetchDailySummary(dateStr) {
  return get(`/daily_summary?target_date=${dateStr}`)
}

/** 获取指定日期的小时级数据 */
export function fetchHourlyRecords(dateStr) {
  return get(`/hourly_records_by_date?target_date=${dateStr}`)
}

/** 手动触发后台抓取 */
export function triggerFetchNow() {
  return fetch(`${BASE}/fetch_now`, { method: "POST" })
}
