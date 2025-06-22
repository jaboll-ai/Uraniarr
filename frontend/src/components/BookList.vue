<template>
  <div class="book-list">
    <div class="book-item" v-for="book in books" :key="book.key">
      <img :src="book.bild" :alt="book.name" class="book-icon" />
      <div class="book-info">
        <span class="book-title">{{ book.name }}</span>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { api } from '@/main.ts'

const route = useRoute()

interface Book {
  name: string
  key: string
  autor_key: string
  reihe_key: string | null
  bild: string
  reihe_position: number | null
}

const books = ref<Book[]>([])

onMounted(async () => {
  try {
    const responseB = await api.get<Book[]>(`/author/${route.params.key}/books`)
    books.value = responseB.data
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
})
</script>

<style scoped>
.book-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 10px;
  border: 1px solid var(--borderColor);
  background-color: var(--offWhite);
  border-radius: 8px;
}

.book-item {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--borderColor);
  border-radius: 8px;
  background-color: var(--backgroundWhite);
}

.book-icon {
  width: 50px;
  height: 50px;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 4px;
}

.book-title {
  font-size: 1rem;
  font-weight: 500;
}
</style>