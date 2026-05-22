/**
 * useChart — ECharts 图表渲染
 */
import { ref, onBeforeUnmount, nextTick } from "vue"
import * as echarts from "echarts"

export function useChart() {
  const chartRef = ref(null)
  let myChart = null

  function initChart(historyData, isToday, hourlyData) {
    if (!chartRef.value) return
    if (myChart) myChart.dispose()

    myChart = echarts.init(chartRef.value)

    let option

    if (isToday) {
      const xLabels = historyData.map((item) => {
        const d = new Date(item.record_time)
        return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`
      })
      const playTimeArr = historyData.map((item) => item.playtime)
      const totalLevelArr = historyData.map((item) => item.total_level)

      option = {
        backgroundColor: "transparent",
        tooltip: {
          trigger: "axis",
          backgroundColor: "#1f2937",
          borderColor: "#374151",
          textStyle: { color: "#f3f4f6" },
        },
        legend: {
          data: ["游玩时间", "总等级"],
          textStyle: { color: "#9ca3af" },
        },
        grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
        xAxis: {
          type: "category",
          boundaryGap: false,
          data: xLabels,
          axisLabel: { color: "#9ca3af" },
          axisLine: { lineStyle: { color: "#4b5563" } },
        },
        yAxis: [
          {
            type: "value",
            name: "时长 (h)",
            axisLabel: { color: "#9ca3af" },
            nameTextStyle: { color: "#9ca3af" },
            splitLine: { lineStyle: { color: "#374151" } },
            scale: true,
          },
          {
            type: "value",
            name: "总等级",
            axisLabel: { color: "#9ca3af" },
            nameTextStyle: { color: "#9ca3af" },
            splitLine: { show: false },
            scale: true,
          },
        ],
        series: [
          {
            name: "游玩时间",
            type: "line",
            data: playTimeArr,
            smooth: true,
            symbol: "circle",
            itemStyle: { color: "#34d399" },
            lineStyle: { width: 3 },
          },
          {
            name: "总等级",
            type: "line",
            yAxisIndex: 1,
            data: totalLevelArr,
            smooth: true,
            symbol: "circle",
            itemStyle: { color: "#60a5fa" },
            lineStyle: { width: 3 },
          },
        ],
      }
    } else {
      const xAxisLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`)
      const mobsKilledSeries = new Array(24).fill(0)
      const playtimeSeries = new Array(24).fill(0)
      const damageDealtSeries = new Array(24).fill(0)

      ;(hourlyData || []).forEach((item) => {
        const hr = item.target_hour
        if (hr >= 0 && hr < 24) {
          mobsKilledSeries[hr] = item.mobs_killed_this_hour
          playtimeSeries[hr] = item.playtime_gained
          damageDealtSeries[hr] = item.damage_dealt_this_hour
        }
      })

      option = {
        backgroundColor: "transparent",
        tooltip: {
          trigger: "axis",
          backgroundColor: "#1f2937",
          borderColor: "#374151",
          textStyle: { color: "#f3f4f6" },
        },
        legend: {
          data: ["刷怪增长", "游玩时间", "Raid输出"],
          textStyle: { color: "#9ca3af" },
        },
        grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
        xAxis: {
          type: "category",
          data: xAxisLabels,
          axisLabel: { color: "#9ca3af" },
          axisLine: { lineStyle: { color: "#4b5563" } },
        },
        yAxis: [
          {
            type: "value",
            name: "数量/伤害",
            axisLabel: { color: "#9ca3af" },
            nameTextStyle: { color: "#9ca3af" },
            splitLine: { lineStyle: { color: "#374151" } },
          },
          {
            type: "value",
            name: "游玩时长 (h)",
            axisLabel: { color: "#9ca3af" },
            nameTextStyle: { color: "#9ca3af" },
            splitLine: { show: false },
            position: "right",
          },
        ],
        series: [
          {
            name: "刷怪增长",
            type: "bar",
            data: mobsKilledSeries,
            itemStyle: { color: "#ef4444" },
          },
          {
            name: "Raid输出",
            type: "line",
            data: damageDealtSeries,
            smooth: true,
            itemStyle: { color: "#f59e0b" },
          },
          {
            name: "游玩时间",
            type: "line",
            yAxisIndex: 1,
            data: playtimeSeries,
            smooth: true,
            symbol: "circle",
            itemStyle: { color: "#10b981" },
            lineStyle: { width: 3 },
          },
        ],
      }
    }

    myChart.setOption(option)
    window.addEventListener("resize", onResize)
  }

  function onResize() {
    if (myChart) myChart.resize()
  }

  onBeforeUnmount(() => {
    if (myChart) myChart.dispose()
    window.removeEventListener("resize", onResize)
  })

  return { chartRef, initChart }
}
