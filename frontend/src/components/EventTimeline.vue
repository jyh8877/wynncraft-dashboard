<script setup>
defineProps({
  eventLogs: { type: Array, default: () => [] },
})
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
      最新动态时间线
    </h2>
    <div
      class="bg-gray-800 rounded-xl border border-gray-700/50 p-5 h-[840px] overflow-y-auto shadow-lg"
    >
      <div
        v-if="eventLogs.length === 0"
        class="text-gray-500 text-center mt-15 text-sm"
      >
        还没有产生变动日志。去游戏里升一级或通关一次 Raid，5分钟后这里就会亮起！
      </div>
      <div v-else class="relative border-l border-gray-700 ml-2 space-y-6">
        <div v-for="log in eventLogs" :key="log.id" class="relative pl-6">
          <span
            class="absolute -left-[5px] top-1.5 w-2 h-2 bg-indigo-500 rounded-full ring-4 ring-gray-800"
          ></span>
          <div class="text-[10px] text-gray-500 mb-1 flex items-center gap-2">
            <span>{{ new Date(log.record_time).toLocaleTimeString() }}</span>
            <span
              class="px-1.5 py-0.2 rounded bg-gray-700 text-indigo-300 font-mono scale-90 origin-left uppercase"
              >{{ log.event_category }}</span
            >
          </div>
          <div class="text-xs text-gray-300 leading-relaxed">
            {{ log.message.split("] ")[1] || log.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
