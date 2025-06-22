<template>
  <div class="series-list">
    <div
      v-for="group in seriesGroups"
      :key="group.series.key"
      class="series-group"
    >
      <h3 class="series-name">{{ group.series.name }}</h3>
      <div class="book-list">
        <div
          v-for="book in group.books"
          :key="book.key"
          class="book-item"
        >
          <img
            :src="book.bild"
            :alt="book.name"
            class="book-icon"
          />
          <div class="book-info">
            <span class="book-title">{{ book.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { api } from '@/main.ts'

interface Series {
  autor_key: string
  key: string
  name: string
}

interface Book {
  name: string
  key: string
  autor_key: string
  reihe_key: string | null
  bild: string
  reihe_position: number | null
}

const route = useRoute()

const seriesGroups = ref<Array<{ series: Series; books: Book[] }>>([])

onMounted(async () => {
  try {
    const { data: seriesList } = await api.get<Series[]>(`/author/${route.params.key}/series`)
    const groups = await Promise.all(
      seriesList.map(async (s) => {
        const { data: books } = await api.get<Book[]>(`/series/${s.key}/books`)
        books.sort((a, b) => (a.reihe_position ?? 0) - (b.reihe_position ?? 0))
        return { series: s, books }
      })
    )
    seriesGroups.value = groups
  } catch (err) {
    console.error('Failed to load series or books', err)
  }
})
</script>

<style scoped>
.series-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
  box-sizing: border-box;
}

.series-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 10px;
  padding-bottom: 20px;
  border: 1px solid var(--borderColor);
  background-color: var(--offWhite);
  border-radius: 8px;
}

.series-name {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 10px 0;
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
