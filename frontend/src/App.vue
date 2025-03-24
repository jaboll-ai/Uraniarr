
<template>
  <TopBar/>
  <div class="content">
    <Sidebar/>
    <div class="page-container">
      <TestPage/>
    </div>
  </div>
  <Sidebar/>
</template>

<script setup lang="ts">
import Sidebar from './components/Sidebar.vue';
import TopBar from './components/TopBar.vue';
import TestPage from './pages/TestPage.vue';
</script>

<style scoped>
.content{
  display: flex;
  flex-direction: row;
}

.page-container{
  padding: 1em;
}
</style>
