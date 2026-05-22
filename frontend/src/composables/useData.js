/**
 * useData — 核心数据状态 + 请求 + 自动刷新
 */
import { ref, computed, onMounted, onBeforeUnmount } from "vue"
import { fetchHistory, fetchLogs } from "../api/client"

export function useData() {
  const dailySummary = ref(null)
  const eventLogs = ref([])
  const historyData = ref([])
  const loading = ref(true)

  let autoRefreshTimer = null

  async function fetchAll() {
    loading.value = true
    try {
      const [history, logs] = await Promise.all([
        fetchHistory(30),
        fetchLogs(15),
      ])
      if (history) historyData.value = history
      if (logs) eventLogs.value = logs
    } catch (err) {
      console.error("获取数据失败:", err)
    } finally {
      loading.value = false
    }
  }

  // 计算最新一条快照
  const latestStats = computed(() => {
    if (historyData.value && historyData.value.length > 0) {
      return historyData.value[historyData.value.length - 1]
    }
    return null
  })

  onMounted(() => {
    fetchAll()
    autoRefreshTimer = setInterval(fetchAll, 300_000) // 5 分钟自动刷新
  })

  onBeforeUnmount(() => {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer)
  })

  return {
    dailySummary,
    eventLogs,
    historyData,
    loading,
    latestStats,
    fetchAll,
  }
}
