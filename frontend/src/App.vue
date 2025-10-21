
<template>
  <TopBar/>
  <Sidebar/>
  <div class="page-container">
    <router-view/>
  </div>
</template>

<script setup lang="ts">
import Sidebar from './components/Sidebar.vue';
import TopBar from './components/TopBar.vue';
</script>

<style scoped>
.page-container{
  display: flex;
  overflow-x: hidden;
  padding: 10px;
  margin-left : 200px;
  margin-top: 60px;
  box-sizing: border-box;
  flex-grow: 1;
}
@media (max-width: 768px) {
  .page-container {
    margin-left : 0;
  }
}
</style>
