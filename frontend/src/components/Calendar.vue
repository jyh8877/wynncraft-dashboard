<script setup>
import { ref, computed, onMounted } from "vue"
import { fetchDailySummary } from "../api/client"

defineProps({
  selectedDate: { type: String, default: "" },
})

const emit = defineEmits(["selectDate"])

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth())
const calendarDataMap = ref({})

const daysInCurrentMonth = computed(() => {
  const firstDayIndex = new Date(
    currentYear.value,
    currentMonth.value,
    1
  ).getDay()
  const totalDays = new Date(
    currentYear.value,
    currentMonth.value + 1,
    0
  ).getDate()
  const arr = []
  for (let i = 0; i < firstDayIndex; i++) arr.push({ day: null, dateStr: null })
  for (let d = 1; d <= totalDays; d++) {
    const ds = `${currentYear.value}-${String(currentMonth.value + 1).padStart(
      2,
      "0"
    )}-${String(d).padStart(2, "0")}`
    arr.push({ day: d, dateStr: ds })
  }
  return arr
})

function changeMonth(offset) {
  currentMonth.value += offset
  if (currentMonth.value > 11) {
    currentMonth.value = 0
    currentYear.value++
  } else if (currentMonth.value < 0) {
    currentMonth.value = 11
    currentYear.value--
  }
  loadMonthSummary()
}

function handleSelect(dateStr) {
  if (!dateStr) return
  emit("selectDate", dateStr)
}

async function loadMonthSummary() {
  const daysInMonth = new Date(
    currentYear.value,
    currentMonth.value + 1,
    0
  ).getDate()
  for (let i = 1; i <= daysInMonth; i++) {
    const dStr = `${currentYear.value}-${String(
      currentMonth.value + 1
    ).padStart(2, "0")}-${String(i).padStart(2, "0")}`
    if (calendarDataMap.value[dStr]) continue
    fetchDailySummary(dStr)
      .then((data) => {
        if (data && data.playtime_gained !== undefined) {
          calendarDataMap.value[dStr] = data
        }
      })
      .catch(() => {})
  }
}

onMounted(loadMonthSummary)
</script>

<template>
  <section
    class="bg-gray-800/40 border border-gray-800 rounded-2xl p-6 shadow-xl"
  >
    <div class="flex justify-between items-center mb-5">
      <h2 class="text-xl font-bold text-gray-200 flex items-center gap-2">
        <span class="w-1 h-5 bg-indigo-500 rounded"></span> 战绩打卡日历
      </h2>
      <div
        class="flex items-center gap-3 bg-gray-950 p-1 rounded-lg border border-gray-800"
      >
        <button
          @click="changeMonth(-1)"
          class="px-2.5 py-1 text-gray-400 hover:text-white hover:bg-gray-800 rounded text-xs cursor-pointer transition"
        >
          &lt;
        </button>
        <span
          class="text-xs font-bold min-w-[85px] text-center text-gray-200"
          >{{ currentYear }}年 {{ currentMonth + 1 }}月</span
        >
        <button
          @click="changeMonth(1)"
          class="px-2.5 py-1 text-gray-400 hover:text-white hover:bg-gray-800 rounded text-xs cursor-pointer transition"
        >
          &gt;
        </button>
      </div>
    </div>

    <div
      class="grid grid-cols-7 gap-2 text-center text-xs font-bold text-gray-500 border-b border-gray-800/60 pb-2 mb-2"
    >
      <div>日</div>
      <div>一</div>
      <div>二</div>
      <div>三</div>
      <div>四</div>
      <div>五</div>
      <div>六</div>
    </div>
    <div class="grid grid-cols-7 gap-2">
      <div
        v-for="(item, idx) in daysInCurrentMonth"
        :key="idx"
        @click="handleSelect(item.dateStr)"
        :class="[
          item.day
            ? 'bg-gray-900/40 border-gray-800/80 hover:border-indigo-500/50 cursor-pointer'
            : 'bg-transparent border-transparent pointer-events-none',
          selectedDate === item.dateStr
            ? 'ring-2 ring-indigo-500 border-transparent bg-indigo-950/20'
            : '',
          'border p-2 rounded-xl min-h-[60px] flex flex-col justify-between transition',
        ]"
      >
        <template v-if="item.day">
          <span
            :class="
              selectedDate === item.dateStr
                ? 'text-indigo-400 font-black'
                : 'text-gray-400'
            "
            class="text-left font-mono text-xs"
            >{{ item.day }}</span
          >
          <div
            v-if="calendarDataMap[item.dateStr]"
            class="text-[9px] text-right space-y-0.5 scale-95 origin-right"
          >
            <div
              class="text-green-400"
              v-if="calendarDataMap[item.dateStr].playtime_gained > 0"
            >
              ⚡{{ calendarDataMap[item.dateStr].playtime_gained }}h
            </div>
            <div
              class="text-red-400"
              v-if="calendarDataMap[item.dateStr].mobs_killed_today > 0"
            >
              ⚔️{{
                calendarDataMap[item.dateStr].mobs_killed_today.toLocaleString()
              }}
            </div>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>
