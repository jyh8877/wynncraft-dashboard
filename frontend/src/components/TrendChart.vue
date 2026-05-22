<script setup>
import { watch, nextTick } from "vue"
import { useChart } from "../composables/useChart"

const props = defineProps({
  historyData: { type: Array, default: () => [] },
  isToday: { type: Boolean, default: false },
  hourlyData: { type: Array, default: () => [] },
})

const { chartRef, initChart } = useChart()

watch(
  () => [props.historyData, props.isToday, props.hourlyData],
  async () => {
    await nextTick()
    initChart(props.historyData, props.isToday, props.hourlyData)
  },
  { deep: true }
)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
      <span class="w-1 h-5 bg-blue-400 rounded"></span>
      {{ isToday ? "肝度与等级高频成长轨迹 (LIVE)" : "当日 24H 精准趋势分布" }}
    </h2>
    <div class="bg-gray-800 p-6 rounded-xl border border-gray-700/50 shadow-lg">
      <div ref="chartRef" class="w-full h-80"></div>
    </div>
  </div>
</template>
