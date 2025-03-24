
<template>
  <div class="card">
    <button type="button" @click="count++">count is {{ count }}</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const count = ref(0)
</script>

<style scoped>

.card{
  top: 0;
  left: 0;
  position: relative;
  background-color: var(--sidebarBackgroundColor);
  height: 100vh;
  width: 200px;
  box-sizing: border-box;
}
</style>
