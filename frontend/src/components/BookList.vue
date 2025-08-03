<template>
  <div class="group">
    <div class="book-list">
      <BookItem
        v-for="book in books"
        :key="book.key"
        :book="book"
        @downloadBook="$emit('downloadBook', $event)"
        @deleteBook="$emit('deleteBook', $event)"
      />
    </div>
  </div>
</template>


<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { api } from '@/main.ts'
import BookItem from '@/components/BookItem.vue'

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
  display: table;
  border-spacing: 0 8px;       /* vertical gutter between rows */
}
.group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 10px;
  padding-bottom: 20px;
  border: 1px solid var(--borderColor);
  background-color: var(--offWhite);
  border-radius: 8px;
}
</style>