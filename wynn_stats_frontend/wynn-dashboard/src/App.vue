<script setup>
import { ref, onMounted, nextTick, computed, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

// ==========================================
// 1. 核心响应式数据
// ==========================================
const dailySummary = ref(null)
const eventLogs = ref([])
const historyData = ref([]) // 始终存放每 5 分钟的最新高频快照
const loading = ref(true)
const activeTab = ref('raids') // 默认选中的明细标签页：raids / guild_raids / ranking
const runtime = ref('')
let runtimeTimer = null
let autoRefreshTimer = null

// --- 日历与历史选择联动状态 ---
const selectedDate = ref(new Date().toISOString().split('T')[0]) // 默认选中当天
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth()) // 0 - 11
const calendarDataMap = ref({}) // 缓存用于日历格子的简报数据
const historyHourlyData = ref([]) // 看历史某天时，存放那天的 24 小时数据

// 判断选中的日期是不是今天
const isSelectedToday = computed(() => {
  const todayStr = new Date().toISOString().split('T')[0]
  return selectedDate.value === todayStr
})

// 原有逻辑：永远获取最新一条历史快照，用于驱动状态灯、当前实时数据面板、三大明细 Tab
const latestStats = computed(() => {
  if (historyData.value && historyData.value.length > 0) {
    return historyData.value[historyData.value.length - 1]
  }
  return null
})

const formatRuntime = (ms) => {
  const days = Math.floor(ms / 86400000)
  const hours = Math.floor((ms % 86400000) / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  return `${days}天 ${String(hours).padStart(2, '0')}时 ${String(minutes).padStart(2, '0')}分 ${String(seconds).padStart(2, '0')}秒`
}

const updateRuntime = () => {
  const startTime = new Date('2026-05-20T00:00:00')
  const now = new Date()
  const diff = Math.max(0, now - startTime)
  runtime.value = formatRuntime(diff)
}

const nameMap = {
  combatSoloLevel: '战斗等级 (单人)', combatGlobalLevel: '战斗等级 (全局)',
  totalSoloLevel: '总等级 (单人)', totalGlobalLevel: '总等级 (全局)',
  professionsSoloLevel: '专业总等级 (单人)', professionsGlobalLevel: '专业总等级 (全局)',
  globalPlayerContent: '全局玩家内容排名', playerContent: '玩家内容分',
  frumaCompletion: 'TWP', frumaSrPlayers: 'TWP速通玩家排名',
  orphionCompletion: 'NOL', orphionSrPlayers: 'NOL速通玩家排名',
  colossusCompletion: 'TCC', colossusSrPlayers: 'TCC速通玩家排名',
  namelessCompletion: 'TNA', namelessSrPlayers: 'TNA速通玩家排名',
  grootslangCompletion: 'NOTG', grootslangSrPlayers: 'NOTG速通玩家排名',
  tailoringLevel: '裁缝等级', armouringLevel: '锻甲等级', jewelingLevel: '珠宝等级',
  miningLevel: '采矿等级', fishingLevel: '钓鱼等级', farmingLevel: '农耕等级',
  woodcuttingLevel: '伐木等级', cookingLevel: '烹饪等级', weaponsmithingLevel: '武器锻造等级',
  woodworkingLevel: '木工等级', alchemismLevel: '炼金等级', scribingLevel: '卷轴抄写等级',
  warsCompletion: '公会战完成度排名',
  'The Canyon Colossus': '峡谷巨像 (The Canyon Colossus)',
  "Orphion's Nexus of Light": '奥菲恩之光枢纽 (Orphion\'s Nexus)',
  'The Nameless Anomaly': '卡死鱼第二爱的tna (The Nameless Anomaly)',
  'Nest of the Grootslangs': '打虫子 (Nest of the Grootslangs)',
  'The Wartorn Palace': '卡死鱼最爱的黄宫 (The Wartorn Palace)'
}

// 图表的 DOM 引用
const chartRef = ref(null)
let myChart = null

// ==========================================
// 2. 智能化图表渲染引擎 (融合实时高频轨迹与历史小时波动)
// ==========================================
const initChart = () => {
  if (!chartRef.value) return
  if (myChart) myChart.dispose()

  myChart = echarts.init(chartRef.value)
  let option = {}

  if (isSelectedToday.value) {
    // 【模式 A：保留原先的今天高频轨迹图功能】
    const xLabels = historyData.value.map(item => {
      const d = new Date(item.record_time)
      return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
    })
    const playTimeArr = historyData.value.map(item => item.playtime)
    const totalLevelArr = historyData.value.map(item => item.total_level)

    option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1f2937', borderColor: '#374151',
        textStyle: { color: '#f3f4f6' }
      },
      legend: { data: ['游玩时间', '总等级'], textStyle: { color: '#9ca3af' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category', boundaryGap: false, data: xLabels,
        axisLabel: { color: '#9ca3af' }, axisLine: { lineStyle: { color: '#4b5563' } }
      },
      yAxis: [
        { type: 'value', name: '时长 (h)', axisLabel: { color: '#9ca3af' }, nameTextStyle: { color: '#9ca3af' }, splitLine: { lineStyle: { color: '#374151' } }, scale: true },
        { type: 'value', name: '总等级', axisLabel: { color: '#9ca3af' }, nameTextStyle: { color: '#9ca3af' }, splitLine: { show: false }, scale: true }
      ],
      series: [
        { name: '游玩时间', type: 'line', data: playTimeArr, smooth: true, symbol: 'circle', itemStyle: { color: '#34d399' }, lineStyle: { width: 3 } },
        { name: '总等级', type: 'line', yAxisIndex: 1, data: totalLevelArr, smooth: true, symbol: 'circle', itemStyle: { color: '#60a5fa' }, lineStyle: { width: 3 } }
      ]
    }
  } else {
    // 【模式 B：看历史日期的 24H 统计柱状/折线图】
    const xAxisLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`)
    const mobsKilledSeries = new Array(24).fill(0)
    const playtimeSeries = new Array(24).fill(0)
    const damageDealtSeries = new Array(24).fill(0)

    historyHourlyData.value.forEach(item => {
      const hr = item.target_hour
      if (hr >= 0 && hr < 24) {
        mobsKilledSeries[hr] = item.mobs_killed_this_hour
        playtimeSeries[hr] = item.playtime_gained
        damageDealtSeries[hr] = item.damage_dealt_this_hour
      }
    })

    option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1f2937', borderColor: '#374151',
        textStyle: { color: '#f3f4f6' }
      },
      legend: { data: ['刷怪增长', '游玩时间', 'Raid输出'], textStyle: { color: '#9ca3af' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: xAxisLabels, axisLabel: { color: '#9ca3af' }, axisLine: { lineStyle: { color: '#4b5563' } } },
      yAxis: [
        { type: 'value', name: '数量/伤害', axisLabel: { color: '#9ca3af' }, nameTextStyle: { color: '#9ca3af' }, splitLine: { lineStyle: { color: '#374151' } } },
        { type: 'value', name: '游玩时长 (h)', axisLabel: { color: '#9ca3af' }, nameTextStyle: { color: '#9ca3af' }, splitLine: { show: false }, position: 'right' }
      ],
      series: [
        { name: '刷怪增长', type: 'bar', data: mobsKilledSeries, itemStyle: { color: '#ef4444' } },
        { name: 'Raid输出', type: 'line', data: damageDealtSeries, smooth: true, itemStyle: { color: '#f59e0b' } },
        { name: '游玩时间', type: 'line', yAxisIndex: 1, data: playtimeSeries, smooth: true, symbol: 'circle', itemStyle: { color: '#10b981' }, lineStyle: { width: 3 } }
      ]
    }
  }
  myChart.setOption(option)
}

// ==========================================
// 3. 数据异步请求核心
// ==========================================
const fetchDetailsByDate = async (dateStr) => {
  try {
    // 1. 拉取指定日期的结算摘要
    const summaryRes = await fetch(`/api/daily_summary?target_date=${dateStr}`)
    if (summaryRes.ok) dailySummary.value = await summaryRes.json()

    // 2. 根据日期类型，智能灌注图表所需数据
    if (dateStr === new Date().toISOString().split('T')[0]) {
      // 如果选中的是今天，重新抓一次最新的完整高频数据作为图表集
      const historyRes = await fetch('/api/history?limit=30')
      if (historyRes.ok) {
        historyData.value = await historyRes.json()
        await nextTick()
        initChart()
      }
    } else {
      // 如果是过去的日子，去拿小时总结持久化表
      const hourlyRes = await fetch(`/api/hourly_records_by_date?target_date=${dateStr}`)
      if (hourlyRes.ok) {
        const resData = await hourlyRes.json()
        historyHourlyData.value = resData.data || []
        await nextTick()
        initChart()
      }
    }
  } catch (error) {
    console.error(`加载 ${dateStr} 详情失败:`, error)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    // 永远保持最新的实时快照刷新 (用于状态灯、首层面板、明细 Tab 的常驻实时功能)
    const historyRes = await fetch('/api/history?limit=30')
    if (historyRes.ok) historyData.value = await historyRes.json()

    // 获取日志
    const logsRes = await fetch('/api/logs?limit=15')
    if (logsRes.ok) eventLogs.value = await logsRes.json()

    // 按选定日期加载图表与战报区域
    await fetchDetailsByDate(selectedDate.value)
    // 预同步当月日历基础打卡点
    fetchMonthSummaryData()
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 异步加载当前日历页所有天数的统计，用来显示小气泡
const fetchMonthSummaryData = async () => {
  const daysInMonth = new Date(currentYear.value, currentMonth.value + 1, 0).getDate()
  for (let i = 1; i <= daysInMonth; i++) {
    const dStr = `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    if (calendarDataMap.value[dStr]) continue
    
    fetch(`/api/daily_summary?target_date=${dStr}`).then(res => {
      if (res.ok) return res.json()
    }).then(data => {
      if (data && data.playtime_gained !== undefined) {
        calendarDataMap.value[dStr] = data
      }
    }).catch(() => {})
  }
}

// ==========================================
// 4. 日历管理计算
// ==========================================
const daysInCurrentMonth = computed(() => {
  const firstDayIndex = new Date(currentYear.value, currentMonth.value, 1).getDay()
  const totalDays = new Date(currentYear.value, currentMonth.value + 1, 0).getDate()
  
  const daysArr = []
  for (let i = 0; i < firstDayIndex; i++) {
    daysArr.push({ day: null, dateStr: null })
  }
  for (let d = 1; d <= totalDays; d++) {
    const dStr = `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    daysArr.push({ day: d, dateStr: dStr })
  }
  return daysArr
})

const changeMonth = (offset) => {
  currentMonth.value += offset
  if (currentMonth.value > 11) {
    currentMonth.value = 0
    currentYear.value++
  } else if (currentMonth.value < 0) {
    currentMonth.value = 11
    currentYear.value--
  }
  fetchMonthSummaryData()
}

const handleDateSelect = (dateStr) => {
  if (!dateStr) return
  selectedDate.value = dateStr
  fetchDetailsByDate(dateStr)
}

window.addEventListener('resize', () => {
  if (myChart) myChart.resize()
})

onMounted(() => {
  fetchData()
  updateRuntime()
  runtimeTimer = setInterval(updateRuntime, 1000)
  
  // 5分钟自动全量静默循环刷新（保持页面永远是最实时的）
  autoRefreshTimer = setInterval(() => {
    fetchData()
  }, 300000)
})

onBeforeUnmount(() => {
  if (runtimeTimer) clearInterval(runtimeTimer)
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
})
</script>

<template>
  <div class="min-h-screen p-8 max-w-7xl mx-auto bg-gray-900 text-gray-100">
    <header class="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end border-b border-gray-800 pb-6 gap-4">
      <div>
        <div class="flex items-center gap-3">
          <h1 class="text-4xl font-extrabold text-amber-400 tracking-wide">Kasyu_pwq</h1>
          <span v-if="latestStats" :class="latestStats.is_online ? 'bg-green-500/10 text-green-400 border-green-500/30' : 'bg-gray-800 text-gray-400 border-gray-700'" class="px-2.5 py-1 text-xs font-bold rounded-full border flex items-center gap-1.5">
            <span :class="latestStats.is_online ? 'bg-green-400 animate-pulse' : 'bg-gray-500'" class="w-2 h-2 rounded-full"></span>
            {{ latestStats.is_online ? `在线 (${latestStats.server})` : '离线' }}
          </span>
          <span v-if="latestStats?.guild_prefix" class="px-2 py-0.5 text-xs font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 rounded">
            [{{ latestStats.guild_prefix }}]
          </span>
        </div>
        <p class="text-gray-400 mt-2 text-sm">我已视奸卡死鱼：{{ runtime }}</p>
      </div>
      
      <div class="flex items-center gap-3">
        <span class="px-4 py-2 bg-gray-800 text-xs border border-gray-700 rounded-lg font-medium text-amber-400 flex items-center gap-1.5">
          📅 当前对齐: <span class="font-bold underline">{{ selectedDate }}</span>
          <span v-if="isSelectedToday" class="ml-1 px-1 py-0.2 text-[9px] bg-green-500/20 text-green-400 rounded border border-green-500/30 font-bold uppercase tracking-wider animate-pulse">LIVE 实时</span>
        </span>
        <button @click="fetchData" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold transition cursor-pointer shadow-lg shadow-indigo-600/20">
          手动刷新数据
        </button>
      </div>
    </header>

    <div v-if="loading && historyData.length === 0" class="text-center text-gray-500 mt-20 text-lg">
      正在接入 Wynncraft 数据矩阵...
    </div>

    <div v-else class="space-y-8">
      
      <section class="bg-gray-800/40 border border-gray-800 rounded-2xl p-6 shadow-xl">
        <div class="flex justify-between items-center mb-5">
          <h2 class="text-xl font-bold text-gray-200 flex items-center gap-2">
            <span class="w-1 h-5 bg-indigo-500 rounded"></span> 战绩打卡日历
          </h2>
          <div class="flex items-center gap-3 bg-gray-950 p-1 rounded-lg border border-gray-800">
            <button @click="changeMonth(-1)" class="px-2.5 py-1 text-gray-400 hover:text-white hover:bg-gray-800 rounded text-xs cursor-pointer transition">&lt;</button>
            <span class="text-xs font-bold min-w-[85px] text-center text-gray-200">{{ currentYear }}年 {{ currentMonth + 1 }}月</span>
            <button @click="changeMonth(1)" class="px-2.5 py-1 text-gray-400 hover:text-white hover:bg-gray-800 rounded text-xs cursor-pointer transition">&gt;</button>
          </div>
        </div>

        <div class="grid grid-cols-7 gap-2 text-center text-xs font-bold text-gray-500 border-b border-gray-800/60 pb-2 mb-2">
          <div>日</div><div>一</div><div>二</div><div>三</div><div>四</div><div>五</div><div>六</div>
        </div>
        <div class="grid grid-cols-7 gap-2">
          <div v-for="(item, idx) in daysInCurrentMonth" :key="idx" 
               @click="handleDateSelect(item.dateStr)"
               :class="[
                 item.day ? 'bg-gray-900/40 border-gray-800/80 hover:border-indigo-500/50 cursor-pointer' : 'bg-transparent border-transparent pointer-events-none',
                 selectedDate === item.dateStr ? 'ring-2 ring-indigo-500 border-transparent bg-indigo-950/20' : '',
                 'border p-2 rounded-xl min-h-[60px] flex flex-col justify-between transition'
               ]">
            <template v-if="item.day">
              <span :class="selectedDate === item.dateStr ? 'text-indigo-400 font-black' : 'text-gray-400'" class="text-left font-mono text-xs">{{ item.day }}</span>
              
              <div v-if="calendarDataMap[item.dateStr]" class="text-[9px] text-right space-y-0.5 scale-95 origin-right">
                <div class="text-green-400" v-if="calendarDataMap[item.dateStr].playtime_gained > 0">⚡{{ calendarDataMap[item.dateStr].playtime_gained }}h</div>
                <div class="text-red-400" v-if="calendarDataMap[item.dateStr].mobs_killed_today > 0">⚔️{{ (calendarDataMap[item.dateStr].mobs_killed_today).toLocaleString() }}</div>
              </div>
            </template>
          </div>
        </div>
      </section>

      <!-- DEBUG: show historyData count and latestStats for troubleshooting -->
      <!-- <div class="mb-4 p-3 bg-red-900/20 border border-red-800 rounded text-xs text-red-300">
        调试: historyData 长度 = {{ historyData.length }} | latestStats = {{ JSON.stringify(latestStats) }}
      </div> -->

      <section>
        <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
          <span class="w-1 h-5 bg-amber-400 rounded"></span> 当前实时数据面板 (实时事实总览)
        </h2>
        <div v-if="latestStats" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">总等级 (Total Lvl)</span>
            <span class="text-2xl font-bold text-blue-400 mt-2">{{ latestStats.total_level }}</span>
          </div>
          <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">累计游玩时间</span>
            <span class="text-2xl font-bold text-green-400 mt-2">{{ latestStats.playtime }} <span class="text-xs text-gray-500">h</span></span>
          </div>
          <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">累计击杀怪物</span>
            <span class="text-2xl font-bold text-red-400 mt-2">{{ latestStats.mobs_killed.toLocaleString() }}</span>
          </div>
          <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">累计开箱数</span>
            <span class="text-2xl font-bold text-yellow-400 mt-2">{{ latestStats.chests_found.toLocaleString() }}</span>
          </div>
          <!-- <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">完成任务总数</span>
            <span class="text-2xl font-bold text-purple-400 mt-2">{{ latestStats.completed_quests }}</span>
          </div> -->
          <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">Raid 累计总伤害</span>
            <span class="text-xl font-bold text-amber-500 mt-2 truncate" :title="latestStats.raid_damage_dealt.toLocaleString()">
              {{ (latestStats.raid_damage_dealt / 100000000).toFixed(1) }} <span class="text-xs font-normal text-gray-500">亿</span>
            </span>
          </div>
        </div>
      </section>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div class="lg:col-span-2 space-y-8">
          
          <div>
            <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
              <span class="w-1 h-5 bg-green-400 rounded"></span> 
              {{ isSelectedToday ? '今日实时战报' : `历史战报总结 (${selectedDate})` }}
            </h2>
            <div v-if="dailySummary && dailySummary.playtime_gained !== undefined" class="bg-gray-800 p-5 rounded-2xl border border-gray-700/40 shadow-md space-y-5">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
                  <div class="text-gray-400 text-xs mb-1">已累计游玩</div>
                  <div class="text-xl font-extrabold text-green-400">+{{ dailySummary.playtime_gained }} h</div>
                </div>
                <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
                  <div class="text-gray-400 text-xs mb-1">已提升等级</div>
                  <div class="text-xl font-extrabold text-blue-400">+{{ dailySummary.levels_gained }} 级</div>
                </div>
                <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
                  <div class="text-gray-400 text-xs mb-1">已击杀怪物</div>
                  <div class="text-xl font-extrabold text-red-400">+{{ (dailySummary.mobs_killed_today || 0).toLocaleString() }}</div>
                </div>
                <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
                  <div class="text-gray-400 text-xs mb-1">已开启宝箱</div>
                  <div class="text-xl font-extrabold text-yellow-400">+{{ dailySummary.chests_found_today }}</div>
                </div>
              </div>

              <div class="border-t border-gray-700/50 pt-4">
                <div class="text-xs font-bold text-gray-400 mb-3 uppercase tracking-wider">⚔️ 该结算周期内通关副本明细</div>
                <div v-if="dailySummary.raids_completed && Object.keys(dailySummary.raids_completed).length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div v-for="(count, rName) in dailySummary.raids_completed" :key="rName" class="flex justify-between items-center bg-gray-900/40 px-4 py-2 rounded-lg border border-gray-800">
                    <span class="text-xs text-gray-300 font-medium">{{ nameMap[rName] || rName }}</span>
                    <span class="text-xs font-bold text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">+ {{ count }} 次</span>
                  </div>
                </div>
                <div v-else class="text-xs text-gray-500 italic">该时段没有通关副本的动态变更。</div>
              </div>
            </div>
            
            <div v-else class="bg-gray-800/30 p-5 rounded-xl text-gray-400 border border-gray-800 text-sm">
              ℹ 正在累积今日首次快照数据。等待自动抓取或手动触发即可生成差值战报。
            </div>
          </div>

          <!-- <div>
            <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
              <span class="w-1 h-5 bg-blue-400 rounded"></span> 
              {{ isSelectedToday ? '肝度与等级高频成长轨迹 (LIVE)' : '当日 24H 精准趋势分布' }}
            </h2>
            <div class="bg-gray-800 p-6 rounded-xl border border-gray-700/50 shadow-lg">
              <div ref="chartRef" class="w-full h-80"></div>
            </div>
          </div> -->

          <div v-if="latestStats">
            <div class="flex border-b border-gray-800 mb-4 gap-2">
              <button @click="activeTab = 'raids'" :class="activeTab === 'raids' ? 'border-amber-400 text-amber-400 font-bold' : 'border-transparent text-gray-400 hover:text-gray-200'" class="py-2.5 px-4 border-b-2 text-sm transition cursor-pointer">
                ⚔ 个人 Raid 通关明细
              </button>
              <button @click="activeTab = 'guild_raids'" :class="activeTab === 'guild_raids' ? 'border-amber-400 text-amber-400 font-bold' : 'border-transparent text-gray-400 hover:text-gray-200'" class="py-2.5 px-4 border-b-2 text-sm transition cursor-pointer">
                🛡 公会 Raid 参与明细
              </button>
              <button @click="activeTab = 'ranking'" :class="activeTab === 'ranking' ? 'border-amber-400 text-amber-400 font-bold' : 'border-transparent text-gray-400 hover:text-gray-200'" class="py-2.5 px-4 border-b-2 text-sm transition cursor-pointer">
                🏆 全技能等级与全服排名
              </button>
            </div>

            <div class="bg-gray-800/40 border border-gray-800 rounded-xl p-5 shadow-inner">
              <div v-if="activeTab === 'raids'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-for="(count, name) in latestStats.raids_data" :key="name" class="flex justify-between items-center bg-gray-800/80 p-3.5 rounded-lg border border-gray-700/30">
                  <span class="text-sm font-medium text-gray-300">{{ nameMap[name] || name }}</span>
                  <span class="text-base font-bold text-amber-400">{{ count }} 次</span>
                </div>
              </div>

              <div v-if="activeTab === 'guild_raids'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-for="(count, name) in latestStats.guild_raids_data" :key="name" class="flex justify-between items-center bg-gray-800/80 p-3.5 rounded-lg border border-gray-700/30">
                  <span class="text-sm font-medium text-gray-300">{{ nameMap[name] || name }}</span>
                  <span class="text-base font-bold text-indigo-400">{{ count }} 次</span>
                </div>
              </div>

              <div v-if="activeTab === 'ranking'" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 max-h-[450px] overflow-y-auto pr-2">
                <div v-for="(val, key) in latestStats.ranking_data" :key="key" class="bg-gray-900/60 p-3 rounded-lg border border-gray-800/80 flex flex-col justify-between gap-1">
                  <span class="text-xs text-gray-400 font-medium truncate" :title="nameMap[key] || key">
                    {{ nameMap[key] || key }}
                  </span>
                  <span :class="key.toLowerCase().includes('level') ? 'text-blue-400' : 'text-yellow-500 font-mono text-sm'" class="text-sm font-bold">
                    {{ key.toLowerCase().includes('level') ? `# ${val}` : `# ${val.toLocaleString()}` }}
                  </span>
                </div>
              </div>
            </div>
          </div>

        </div>

        <div>
          <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span> 最新动态时间线
          </h2>
          <div class="bg-gray-800 rounded-xl border border-gray-700/50 p-5 h-[840px] overflow-y-auto shadow-lg">
            <div v-if="eventLogs.length === 0" class="text-gray-500 text-center mt-15 text-sm">
              还没有产生变动日志。去游戏里升一级或通关一次 Raid，5分钟后这里就会亮起！
            </div>
            <div v-else class="relative border-l border-gray-700 ml-2 space-y-6">
              <div v-for="log in eventLogs" :key="log.id" class="relative pl-6">
                <span class="absolute -left-[5px] top-1.5 w-2 h-2 bg-indigo-500 rounded-full ring-4 ring-gray-800"></span>
                <div class="text-[10px] text-gray-500 mb-1 flex items-center gap-2">
                  <span>{{ new Date(log.record_time).toLocaleTimeString() }}</span>
                  <span class="px-1.5 py-0.2 rounded bg-gray-700 text-indigo-300 font-mono scale-90 origin-left uppercase">{{ log.event_category }}</span>
                </div>
                <div class="text-xs text-gray-300 leading-relaxed">
                  {{ log.message.split('] ')[1] || log.message }}
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>