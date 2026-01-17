
<template>
  <div class="sidebar" :style="sidebarStyle">
    <router-link to="/" custom v-slot="{ navigate, isActive }">
      <button class="sidebar-button" :class="{ active: isActive }" @click="navigate" type="button">
        Library
      </button>
    </router-link>

    <router-link to="/settings" custom v-slot="{ navigate, isActive }">
      <button class="sidebar-button" :class="{ active: isActive }" @click="navigate" type="button">
        Settings
      </button>
    </router-link>
    <router-link to="/blocklist" custom v-slot="{ navigate, isActive }">
      <button class="sidebar-button" :class="{ active: isActive }" @click="navigate" type="button">
        Blocklist
      </button>
    </router-link>
    <router-link to="/activity" custom v-slot="{ navigate, isActive }">
      <button class="sidebar-button" :class="{ active: isActive }" @click="navigate" type="button">
        Activity
      </button>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useSidebar } from '@/components/sidebar.ts'
const { isOpen } = useSidebar()
const isMobile = ref(window.innerWidth <= 768)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
const sidebarStyle = computed(() => ({
  transform:
    !isMobile.value || isOpen.value
      ? 'translateX(0)'
      : 'translateX(-100%)',
  transition: 'transform 0.3s ease-in-out',
}))
</script>

<style scoped>
.sidebar{
  position: fixed;
  top: 60px;
  z-index: 2;
  height: 100vh;
  width: 200px;
  background-color: var(--lightGray);
  transform: translateX(0);
  transition: transform 0.3s ease;
  display:flex;
  flex-direction: column;
}

.sidebar-button{
  color: #BBB;
  border-radius: 0px;
}
.sidebar-button:hover{
  color: var(--mainColor);
}
.active{
  background-color: var(--darkGray);
  color: var(--mainColor)
}
.active:hover{
  color: color-mix(in srgb, var(--mainColor) 60%, white 40%);;
}
</style>
