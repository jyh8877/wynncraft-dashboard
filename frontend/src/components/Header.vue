<script setup>
import { PLAYER_IGN, PLAYER_NAME } from "../config/constants"

defineProps({
  latestStats: { type: Object, default: null },
  runtime: { type: String, default: "" },
  selectedDate: { type: String, default: "" },
  isSelectedToday: { type: Boolean, default: false },
})

defineEmits(["refresh"])
</script>

<template>
  <header
    class="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end border-b border-gray-800 pb-6 gap-4"
  >
    <div>
      <div class="flex items-center gap-3">
        <h1 class="text-4xl font-extrabold text-amber-400 tracking-wide">
          {{ PLAYER_IGN }}
        </h1>
        <span
          v-if="latestStats"
          :class="
            latestStats.is_online
              ? 'bg-green-500/10 text-green-400 border-green-500/30'
              : 'bg-gray-800 text-gray-400 border-gray-700'
          "
          class="px-2.5 py-1 text-xs font-bold rounded-full border flex items-center gap-1.5"
        >
          <span
            :class="
              latestStats.is_online
                ? 'bg-green-400 animate-pulse'
                : 'bg-gray-500'
            "
            class="w-2 h-2 rounded-full"
          ></span>
          {{ latestStats.is_online ? `在线 (${latestStats.server})` : "离线" }}
        </span>
        <span
          v-if="latestStats?.guild_prefix"
          class="px-2 py-0.5 text-xs font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 rounded"
        >
          [{{ latestStats.guild_prefix }}]
        </span>
      </div>
      <p class="text-gray-400 mt-2 text-sm">我已视奸{{ PLAYER_NAME }}：{{ runtime }}</p>
    </div>

    <div class="flex items-center gap-3">
      <span
        class="px-4 py-2 bg-gray-800 text-xs border border-gray-700 rounded-lg font-medium text-amber-400 flex items-center gap-1.5"
      >
        📅 当前对齐:
        <span class="font-bold underline">{{ selectedDate }}</span>
        <span
          v-if="isSelectedToday"
          class="ml-1 px-1 py-0.2 text-[9px] bg-green-500/20 text-green-400 rounded border border-green-500/30 font-bold uppercase tracking-wider animate-pulse"
        >
          LIVE 实时
        </span>
      </span>
      <button
        @click="$emit('refresh')"
        class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold transition cursor-pointer shadow-lg shadow-indigo-600/20"
      >
        手动刷新数据
      </button>
    </div>
  </header>
</template>
