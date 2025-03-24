<template>
    <div class="top-bar">
        <input
            v-model="search"
            @input="handleInput"
            @keyup.enter="handleSubmit"
            type="text"
            placeholder="Search..."
            class="search-input"
        />
    </div>
</template>


<script setup lang="ts">
import { ref } from 'vue'

const search = ref<string>('')

function handleInput(): void {
  console.log(search.value)
}

function handleSubmit(): void {
  console.log(search.value+" entered")
}
</script>

<style scoped>
.search-input {
  border: 1px solid #ccc;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.top-bar{
    background-color: var(--mainColor);
    width: 100vw;
    height: 60px;
}
</style>