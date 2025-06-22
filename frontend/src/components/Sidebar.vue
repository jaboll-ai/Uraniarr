
<template>
  <div class="sidebar" :style="sidebarStyle">
    <div class="button-wrapper">
      <router-link to="/" custom v-slot="{ navigate, isActive }">
        <button class="sidebar-button" :class="{ active: isActive }" @click="navigate" type="button">
          Library
        </button>
      </router-link>
    </div>

    <div class="button-wrapper">
      <router-link to="/settings" custom v-slot="{ navigate, isActive }">
        <button class="sidebar-button" :class="{ active: isActive }" @click="navigate" type="button">
          Settings
        </button>
      </router-link>
    </div>

    <div class="button-wrapper">
      <router-link to="/activity" custom v-slot="{ navigate, isActive }">
        <button class="sidebar-button" :class="{ active: isActive }" @click="navigate" type="button">
          Activity
        </button>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useSidebar } from './sidebar.ts'
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
}

.active{
  background-color: var(--darkGray);
  color: color-mix(in srgb, var(--mainColor) 80%, black 20%);;
}
.active:hover{
  color: var(--mainColor);
}
</style>
