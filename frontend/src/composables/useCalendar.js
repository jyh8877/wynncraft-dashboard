/**
 * useCalendar — 日历共享工具
 */
import { ref, computed } from "vue"

export function useCalendar() {
  const selectedDate = ref(new Date().toISOString().split("T")[0])

  const isSelectedToday = computed(() => {
    return selectedDate.value === new Date().toISOString().split("T")[0]
  })

  function setSelectedDate(dateStr) {
    if (dateStr) selectedDate.value = dateStr
  }

  return { selectedDate, isSelectedToday, setSelectedDate }
}
