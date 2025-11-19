
<template>
  <notifications position="bottom right" />
  <TopBar/>
  <Sidebar/>
  <div class="page-container">
    <router-view/>
  </div>
</template>

<script setup lang="ts">
import { Notifications } from '@kyvg/vue3-notification';
import Sidebar from './components/Sidebar.vue';
import TopBar from './components/TopBar.vue';
if ((localStorage.getItem('audio')?? "true") === "true") {
  document.documentElement.style.removeProperty('--mainColor');
} else {
  document.documentElement.style.setProperty('--mainColor', '#be8e8e');
}
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
