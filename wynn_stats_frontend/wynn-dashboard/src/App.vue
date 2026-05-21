<script setup>
import { ref, onMounted, nextTick, computed, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

// 响应式数据
const dailySummary = ref(null)
const eventLogs = ref([])
const historyData = ref([])
const loading = ref(true)
const activeTab = ref('raids') // 默认选中的明细标签页：raids / guild_raids / ranking
const runtime = ref('')
let runtimeTimer = null

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

// 英文键名到中文名的翻译字典
const nameMap = {
  // 职业与排名翻译
  combatSoloLevel: '战斗等级 (单人)',
  combatGlobalLevel: '战斗等级 (全局)',
  totalSoloLevel: '总等级 (单人)',
  totalGlobalLevel: '总等级 (全局)',
  professionsSoloLevel: '专业总等级 (单人)',
  professionsGlobalLevel: '专业总等级 (全局)',
  globalPlayerContent: '全局玩家内容排名',
  playerContent: '玩家内容分',
  frumaCompletion: 'TWP',
  frumaSrPlayers: 'TWP速通玩家排名',
  orphionCompletion: 'NOL',
  orphionSrPlayers: 'NOL速通玩家排名',
  colossusCompletion: 'TCC',
  colossusSrPlayers: 'TCC速通玩家排名',
  namelessCompletion: 'TNA',
  namelessSrPlayers: 'TNA速通玩家排名',
  grootslangCompletion: 'NOTG',
  grootslangSrPlayers: 'NOTG速通玩家排名',
  tailoringLevel: '裁缝等级',
  armouringLevel: '锻甲等级',
  jewelingLevel: '珠宝等级',
  miningLevel: '采矿等级',
  fishingLevel: '钓鱼等级',
  farmingLevel: '农耕等级',
  woodcuttingLevel: '伐木等级',
  cookingLevel: '烹饪等级',
  weaponsmithingLevel: '武器锻造等级',
  woodworkingLevel: '木工等级',
  alchemismLevel: '炼金等级',
  scribingLevel: '卷轴抄写等级',
  warsCompletion: '公会战完成度排名',

  // 副本翻译
  'The Canyon Colossus': '峡谷巨像 (The Canyon Colossus)',
  "Orphion's Nexus of Light": '奥菲恩之光枢纽 (Orphion\'s Nexus)',
  'The Nameless Anomaly': '卡死鱼第二爱的tna (The Nameless Anomaly)',
  'Nest of the Grootslangs': '打虫子 (Nest of the Grootslangs)',
  'The Wartorn Palace': '卡死鱼最爱的黄宫 (The Wartorn Palace)'
}

// 计算属性：获取最新一条历史记录
const latestStats = computed(() => {
  if (historyData.value && historyData.value.length > 0) {
    return historyData.value[historyData.value.length - 1]
  }
  return null
})

// 图表的 DOM 引用
const chartRef = ref(null)
let myChart = null

// 初始化 ECharts 图表
const initChart = (data) => {
  if (!chartRef.value || data.length === 0) return
  if (myChart) myChart.dispose()

  myChart = echarts.init(chartRef.value)

  const xLabels = data.map(item => {
    const d = new Date(item.record_time)
    return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  })
  const playTimeArr = data.map(item => item.playtime)
  const totalLevelArr = data.map(item => item.total_level)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f2937',
      borderColor: '#374151',
      textStyle: { color: '#f3f4f6' }
    },
    legend: {
      data: ['游玩时间', '总等级'],
      textStyle: { color: '#9ca3af' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xLabels,
      axisLabel: { color: '#9ca3af' },
      axisLine: { lineStyle: { color: '#4b5563' } }
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
  myChart.setOption(option)
}

const fetchData = async () => {
  loading.value = true
  try {
    const summaryRes = await fetch('/api/daily_summary')
    if (summaryRes.ok) dailySummary.value = await summaryRes.json()

    const logsRes = await fetch('/api/logs?limit=15')
    if (logsRes.ok) eventLogs.value = await logsRes.json()

    const historyRes = await fetch('/api/history?limit=30')
    if (historyRes.ok) {
      historyData.value = await historyRes.json()
      await nextTick()
      initChart(historyData.value)
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

window.addEventListener('resize', () => {
  if (myChart) myChart.resize()
})

onMounted(() => {
  fetchData()
  updateRuntime()
  runtimeTimer = setInterval(updateRuntime, 1000)
})

onBeforeUnmount(() => {
  if (runtimeTimer) {
    clearInterval(runtimeTimer)
    runtimeTimer = null
  }
})
</script>

<template>
  <div class="min-h-screen p-8 max-w-7xl mx-auto">
    <!-- 1. 头部区域与实时状态灯 -->
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
      <button @click="fetchData" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold transition cursor-pointer shadow-lg shadow-indigo-600/20">
        手动刷新数据
      </button>
    </header>

    <div v-if="loading && historyData.length === 0" class="text-center text-gray-500 mt-20 text-lg">
      正在接入 Wynncraft 数据矩阵...
    </div>

    <div v-else class="space-y-8">
      
      <!-- 2. 当前实时数据面板 -->
      <section>
        <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
          <span class="w-1 h-5 bg-amber-400 rounded"></span> 当前实时数据面板
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
          <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">完成任务总数</span>
            <span class="text-2xl font-bold text-purple-400 mt-2">{{ latestStats.completed_quests }}</span>
          </div>
          <div class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between">
            <span class="text-gray-400 text-xs font-medium">Raid 累计总伤害</span>
            <span class="text-xl font-bold text-amber-500 mt-2 truncate" :title="latestStats.raid_damage_dealt.toLocaleString()">
              {{ (latestStats.raid_damage_dealt / 100000000).toFixed(1) }} <span class="text-xs font-normal text-gray-500">亿</span>
            </span>
          </div>
        </div>
      </section>

      <!-- 3. 下方混合布局 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- 左侧及中间：战报 + 历史折线图 + 明细标签页 -->
        <div class="lg:col-span-2 space-y-8">
          
          <!-- 今日战报 -->
          <div>
            <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
              <span class="w-1 h-5 bg-green-400 rounded"></span> 今日战报 ({{ dailySummary?.date || '计算中' }})
            </h2>
            <div v-if="dailySummary && dailySummary.playtime_gained !== undefined" class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-gray-800 p-4 rounded-xl border border-gray-700/50 shadow-md">
                <div class="text-gray-400 text-xs mb-1">今日游玩</div>
                <div class="text-xl font-extrabold text-green-400">+{{ dailySummary.playtime_gained }} h</div>
              </div>
              <div class="bg-gray-800 p-4 rounded-xl border border-gray-700/50 shadow-md">
                <div class="text-gray-400 text-xs mb-1">今日升级</div>
                <div class="text-xl font-extrabold text-blue-400">+{{ dailySummary.levels_gained }} 级</div>
              </div>
              <div class="bg-gray-800 p-4 rounded-xl border border-gray-700/50 shadow-md">
                <div class="text-gray-400 text-xs mb-1">今日杀怪</div>
                <div class="text-xl font-extrabold text-red-400">+{{ dailySummary.mobs_killed_today }}</div>
              </div>
              <div class="bg-gray-800 p-4 rounded-xl border border-gray-700/50 shadow-md">
                <div class="text-gray-400 text-xs mb-1">今日开箱</div>
                <div class="text-xl font-extrabold text-yellow-400">+{{ dailySummary.chests_found_today }}</div>
              </div>
            </div>
            <div v-else class="bg-gray-800/30 p-5 rounded-xl text-gray-400 border border-gray-800 text-sm">
              ℹ 正在累积今日首次快照数据。等待自动抓取或手动触发即可生成差值战报。
            </div>
          </div>

          <!-- 历史趋势折线图 -->
          <div>
            <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
              <span class="w-1 h-5 bg-blue-400 rounded"></span> 肝度与等级成长轨迹
            </h2>
            <div class="bg-gray-800 p-6 rounded-xl border border-gray-700/50 shadow-lg">
              <div ref="chartRef" class="w-full h-80"></div>
            </div>
          </div>

          <!-- 新增：详细成就分类面板 (Tabs) -->
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
              <!-- Tab 1: 个人 Raid 列表 -->
              <div v-if="activeTab === 'raids'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-for="(count, name) in latestStats.raids_data" :key="name" class="flex justify-between items-center bg-gray-800/80 p-3.5 rounded-lg border border-gray-700/30">
                  <span class="text-sm font-medium text-gray-300">{{ nameMap[name] || name }}</span>
                  <span class="text-base font-bold text-amber-400">{{ count }} 次</span>
                </div>
              </div>

              <!-- Tab 2: 公会 Raid 列表 -->
              <div v-if="activeTab === 'guild_raids'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-for="(count, name) in latestStats.guild_raids_data" :key="name" class="flex justify-between items-center bg-gray-800/80 p-3.5 rounded-lg border border-gray-700/30">
                  <span class="text-sm font-medium text-gray-300">{{ nameMap[name] || name }}</span>
                  <span class="text-base font-bold text-indigo-400">{{ count }} 次</span>
                </div>
              </div>

              <!-- Tab 3: 全服全技能排行 -->
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

        <!-- 右侧：动态时间线 -->
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