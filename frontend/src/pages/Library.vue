<template>
  <div class="authors">
    <AuthorCard
      v-for="author in authors"
      :key="author.key"
      :author="author"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AuthorCard from './components/AuthorCard.vue'
import { api } from '../main.ts'

interface Author {
  name: string
  key: string
  bild: string
  bio: string
}

const authors = ref<Author[]>([])
onMounted(async () => {
  const response = await api.get<Author[]>('/authors')
  authors.value = response.data
})
</script>

<style scoped>
.authors {
  flex-grow: 1;
  display: grid;
  grid-template-columns: repeat(auto-fit, 250px);
  grid-auto-rows: 250px;
  gap: 16px;
  padding: 16px;
}
</style>