<script setup>
import { ref } from "vue"
import { RAID_NAME_MAP, RANKING_NAME_MAP } from "../config/constants"

defineProps({
  latestStats: { type: Object, default: null },
})

const activeTab = ref("raids")
</script>

<template>
  <div v-if="latestStats">
    <div class="flex border-b border-gray-800 mb-4 gap-2">
      <button
        @click="activeTab = 'raids'"
        :class="
          activeTab === 'raids'
            ? 'border-amber-400 text-amber-400 font-bold'
            : 'border-transparent text-gray-400 hover:text-gray-200'
        "
        class="py-2.5 px-4 border-b-2 text-sm transition cursor-pointer"
      >
        ⚔ 个人 Raid 通关明细
      </button>
      <button
        @click="activeTab = 'guild_raids'"
        :class="
          activeTab === 'guild_raids'
            ? 'border-amber-400 text-amber-400 font-bold'
            : 'border-transparent text-gray-400 hover:text-gray-200'
        "
        class="py-2.5 px-4 border-b-2 text-sm transition cursor-pointer"
      >
        🛡 公会 Raid 参与明细
      </button>
      <button
        @click="activeTab = 'ranking'"
        :class="
          activeTab === 'ranking'
            ? 'border-amber-400 text-amber-400 font-bold'
            : 'border-transparent text-gray-400 hover:text-gray-200'
        "
        class="py-2.5 px-4 border-b-2 text-sm transition cursor-pointer"
      >
        🏆 全技能等级与全服排名
      </button>
    </div>

    <div
      class="bg-gray-800/40 border border-gray-800 rounded-xl p-5 shadow-inner"
    >
      <!-- 个人 Raid 明细 -->
      <div
        v-if="activeTab === 'raids'"
        class="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        <div
          v-for="(count, name) in latestStats.raids_data"
          :key="name"
          class="flex justify-between items-center bg-gray-800/80 p-3.5 rounded-lg border border-gray-700/30"
        >
          <span class="text-sm font-medium text-gray-300">{{
            RAID_NAME_MAP[name] || name
          }}</span>
          <span class="text-base font-bold text-amber-400">{{ count }} 次</span>
        </div>
      </div>

      <!-- 公会 Raid 明细 -->
      <div
        v-if="activeTab === 'guild_raids'"
        class="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        <div
          v-for="(count, name) in latestStats.guild_raids_data"
          :key="name"
          class="flex justify-between items-center bg-gray-800/80 p-3.5 rounded-lg border border-gray-700/30"
        >
          <span class="text-sm font-medium text-gray-300">{{
            RAID_NAME_MAP[name] || name
          }}</span>
          <span class="text-base font-bold text-indigo-400"
            >{{ count }} 次</span
          >
        </div>
      </div>

      <!-- 全技能等级与排名 -->
      <div
        v-if="activeTab === 'ranking'"
        class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 max-h-[450px] overflow-y-auto pr-2"
      >
        <div
          v-for="(val, key) in latestStats.ranking_data"
          :key="key"
          class="bg-gray-900/60 p-3 rounded-lg border border-gray-800/80 flex flex-col justify-between gap-1"
        >
          <span class="text-xs text-gray-400 font-medium truncate" :title="RANKING_NAME_MAP[key] || key">
            {{ RANKING_NAME_MAP[key] || key }}
          </span>
          <span
            :class="
              key.toLowerCase().includes('level')
                ? 'text-blue-400'
                : 'text-yellow-500 font-mono text-sm'
            "
            class="text-sm font-bold"
          >
            {{ key.toLowerCase().includes("level") ? `# ${val}` : `# ${val.toLocaleString()}` }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
