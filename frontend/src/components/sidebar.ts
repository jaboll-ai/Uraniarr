import { ref } from 'vue'

const isOpen = ref(false)

export function toggleSidebar() {
  isOpen.value = !isOpen.value
}
export function useSidebar() {
  return { isOpen, toggleSidebar }
}
