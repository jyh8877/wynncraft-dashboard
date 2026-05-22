<script setup>
defineProps({
  latestStats: { type: Object, default: null },
})
</script>

<template>
  <section>
    <h2
      class="text-xl font-bold text-gray-300 mb-4 flex items-center gap-2"
    >
      <span class="w-1 h-5 bg-amber-400 rounded"></span>
      当前实时数据面板 (实时事实总览)
    </h2>
    <div
      v-if="latestStats"
      class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
    >
      <div
        class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between"
      >
        <span class="text-gray-400 text-xs font-medium"
          >总等级 (Total Lvl)</span
        >
        <span class="text-2xl font-bold text-blue-400 mt-2">{{
          latestStats.total_level
        }}</span>
      </div>
      <div
        class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between"
      >
        <span class="text-gray-400 text-xs font-medium">累计游玩时间</span>
        <span class="text-2xl font-bold text-green-400 mt-2"
          >{{ latestStats.playtime }}
          <span class="text-xs text-gray-500">h</span></span
        >
      </div>
      <div
        class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between"
      >
        <span class="text-gray-400 text-xs font-medium">累计击杀怪物</span>
        <span class="text-2xl font-bold text-red-400 mt-2">{{
          latestStats.mobs_killed.toLocaleString()
        }}</span>
      </div>
      <div
        class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between"
      >
        <span class="text-gray-400 text-xs font-medium">累计开箱数</span>
        <span class="text-2xl font-bold text-yellow-400 mt-2">{{
          latestStats.chests_found.toLocaleString()
        }}</span>
      </div>
      <div
        class="bg-gray-800/50 p-4 rounded-xl border border-gray-800 flex flex-col justify-between"
      >
        <span class="text-gray-400 text-xs font-medium">Raid 累计总伤害</span>
        <span
          class="text-xl font-bold text-amber-500 mt-2 truncate"
          :title="latestStats.raid_damage_dealt.toLocaleString()"
        >
          {{ (latestStats.raid_damage_dealt / 100000000).toFixed(1) }}
          <span class="text-xs font-normal text-gray-500">亿</span>
        </span>
      </div>
    </div>
    <div v-else class="text-gray-500 text-sm">
      等待数据加载…
    </div>
  </section>
</template>
