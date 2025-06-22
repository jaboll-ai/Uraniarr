<template>
    <div class="top-bar">
        <div class="logo">
          <img class="logo-image" src="/lesarr.svg" alt="Logo" />
        </div>
        <div class="menu">
          <button class="material-icons topbutton"  @click="toggleSidebar()">menu</button>
        </div>
        <div class="search">
          <div class="search-icon material-icons">search</div>
          <input
              v-model="search"
              @input="handleInput"
              @keyup.enter="handleSubmit"
              type="text"
              placeholder="Search..."
              class="search-input"
          />
        </div>
    </div>
</template>


<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { toggleSidebar } from './sidebar'


const search = ref<string>('')
const router = useRouter()

function handleInput(): void {
  console.log(search.value)
}

function handleSubmit(): void {
  console.log(search.value+" entered")
  router.push({ name: 'Search', query: { q: search.value } })
}
</script>

<style scoped>
.search {
  display: flex;
  align-items: center;
}

.search-input {
  border: none;
  padding: 6px 10px;
  font-size: 14px;
  outline: none;
  background-color: transparent;
}
.search-input,
.search-icon,
.search-input::placeholder {
  color: var(--textWhite);
}

.logo{
  display: flex;
  align-items: center;
  flex: 0 0 200px;
  padding-left: 20px;
  box-sizing: border-box;
}

.logo-image{
  width: 32px;
  height: 32px;
}

.top-bar{
  position: fixed;
  z-index: 3;
  display: flex;
  align-items: center;
  width: 100%;
  background-color: var(--mainColor);
  height: 60px;
}
.topbutton{
  background-color: transparent;
}
.topbutton:hover{
  color: var(--sidebarBackgroundColor)
}

.menu{
  display: none;
}
@media (max-width: 768px) {
  .menu {
    display: block;
    flex: 0 0 45px;
  }
  .logo {
    flex: 0 0 60px;
  }
}
</style>