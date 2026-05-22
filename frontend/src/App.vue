<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue"

import { RUNTIME_START } from "./config/constants"
import { useData } from "./composables/useData"
import { useCalendar } from "./composables/useCalendar"
import { fetchDailySummary, fetchHourlyRecords } from "./api/client"

import Header from "./components/Header.vue"
import Calendar from "./components/Calendar.vue"
import StatsPanel from "./components/StatsPanel.vue"
import DailyReport from "./components/DailyReport.vue"
import DetailTabs from "./components/DetailTabs.vue"
import EventTimeline from "./components/EventTimeline.vue"
import TrendChart from "./components/TrendChart.vue"

// ── 状态 ──────────────────────────────────────────────────
const { dailySummary, eventLogs, historyData, loading, latestStats, fetchAll } =
  useData()

const { selectedDate, isSelectedToday, setSelectedDate } = useCalendar()

const runtime = ref("")
let runtimeTimer = null

// ── 运行时时钟 ────────────────────────────────────────────
function formatRuntime(ms) {
  const days = Math.floor(ms / 86400000)
  const hours = Math.floor((ms % 86400000) / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  return `${days}天 ${String(hours).padStart(2, "0")}时 ${String(minutes).padStart(2, "0")}分 ${String(seconds).padStart(2, "0")}秒`
}

function updateRuntime() {
  const startTime = new Date(RUNTIME_START)
  const now = new Date()
  runtime.value = formatRuntime(Math.max(0, now - startTime))
}

// ── 日期选择 → 数据加载 ──────────────────────────────────
async function onSelectDate(dateStr) {
  setSelectedDate(dateStr)
  await loadDateDetails(dateStr)
}

async function loadDateDetails(dateStr) {
  const today = new Date().toISOString().split("T")[0]
  const res = await fetchDailySummary(dateStr)
  if (res && res.playtime_gained !== undefined) {
    dailySummary.value = res
  } else {
    dailySummary.value = res // 可能是 { message: ... }
  }

  if (dateStr === today) {
    // 今天：保持已有 historyData（由 useData 自动刷新）
    historyData.value._hourly = []
  } else {
    // 历史日期：加载小时数据
    const hourlyRes = await fetchHourlyRecords(dateStr)
    historyData.value._hourly = hourlyRes?.data || []
  }
}

async function handleRefresh() {
  await fetchAll()
  await loadDateDetails(selectedDate.value)
}

// ── 生命周期 ──────────────────────────────────────────────
onMounted(() => {
  updateRuntime()
  runtimeTimer = setInterval(updateRuntime, 1000)
  loadDateDetails(selectedDate.value)
})

onBeforeUnmount(() => {
  if (runtimeTimer) clearInterval(runtimeTimer)
})
</script>

<template>
  <div class="min-h-screen p-8 max-w-7xl mx-auto bg-gray-900 text-gray-100">
    <Header
      :latestStats="latestStats"
      :runtime="runtime"
      :selectedDate="selectedDate"
      :isSelectedToday="isSelectedToday"
      @refresh="handleRefresh"
    />

    <div
      v-if="loading && historyData.length === 0"
      class="text-center text-gray-500 mt-20 text-lg"
    >
      正在接入 Wynncraft 数据矩阵…
    </div>

    <div v-else class="space-y-8">
      <Calendar :selectedDate="selectedDate" @selectDate="onSelectDate" />

      <StatsPanel :latestStats="latestStats" />

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-8">
          <DailyReport
            :dailySummary="dailySummary"
            :selectedDate="selectedDate"
            :isSelectedToday="isSelectedToday"
          />

          <TrendChart
            :historyData="historyData"
            :isToday="isSelectedToday"
            :hourlyData="historyData._hourly || []"
          />

          <DetailTabs :latestStats="latestStats" />
        </div>

        <EventTimeline :eventLogs="eventLogs" />
      </div>
    </div>
  </div>
</template>
