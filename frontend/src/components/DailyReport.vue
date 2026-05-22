<script setup>
import { RAID_NAME_MAP } from "../config/constants"

defineProps({
  dailySummary: { type: Object, default: null },
  selectedDate: { type: String, default: "" },
  isSelectedToday: { type: Boolean, default: false },
})
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2">
      <span class="w-1 h-5 bg-green-400 rounded"></span>
      {{ isSelectedToday ? "今日实时战报" : `历史战报总结 (${selectedDate})` }}
    </h2>
    <div
      v-if="dailySummary && dailySummary.playtime_gained !== undefined"
      class="bg-gray-800 p-5 rounded-2xl border border-gray-700/40 shadow-md space-y-5"
    >
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
          <div class="text-gray-400 text-xs mb-1">已累计游玩</div>
          <div class="text-xl font-extrabold text-green-400">
            +{{ dailySummary.playtime_gained }} h
          </div>
        </div>
        <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
          <div class="text-gray-400 text-xs mb-1">已提升等级</div>
          <div class="text-xl font-extrabold text-blue-400">
            +{{ dailySummary.levels_gained }} 级
          </div>
        </div>
        <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
          <div class="text-gray-400 text-xs mb-1">已击杀怪物</div>
          <div class="text-xl font-extrabold text-red-400">
            +{{ (dailySummary.mobs_killed_today || 0).toLocaleString() }}
          </div>
        </div>
        <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
          <div class="text-gray-400 text-xs mb-1">已开启宝箱</div>
          <div class="text-xl font-extrabold text-yellow-400">
            +{{ dailySummary.chests_found_today }}
          </div>
        </div>
      </div>

      <div class="border-t border-gray-700/50 pt-4">
        <div class="text-xs font-bold text-gray-400 mb-3 uppercase tracking-wider">
          ⚔️ 该结算周期内通关副本明细
        </div>
        <div
          v-if="
            dailySummary.raids_completed &&
            Object.keys(dailySummary.raids_completed).length > 0
          "
          class="grid grid-cols-1 md:grid-cols-2 gap-3"
        >
          <div
            v-for="(count, rName) in dailySummary.raids_completed"
            :key="rName"
            class="flex justify-between items-center bg-gray-900/40 px-4 py-2 rounded-lg border border-gray-800"
          >
            <span class="text-xs text-gray-300 font-medium">{{
              RAID_NAME_MAP[rName] || rName
            }}</span>
            <span
              class="text-xs font-bold text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20"
              >+ {{ count }} 次</span
            >
          </div>
        </div>
        <div v-else class="text-xs text-gray-500 italic">
          该时段没有通关副本的动态变更。
        </div>
      </div>
    </div>
    <div
      v-else-if="dailySummary && dailySummary.message"
      class="bg-gray-800/30 p-5 rounded-xl text-gray-400 border border-gray-800 text-sm"
    >
      ℹ {{ dailySummary.message }}
    </div>
    <div
      v-else
      class="bg-gray-800/30 p-5 rounded-xl text-gray-400 border border-gray-800 text-sm"
    >
      ℹ 正在累积今日首次快照数据。等待自动抓取或手动触发即可生成差值战报。
    </div>
  </div>
</template>
