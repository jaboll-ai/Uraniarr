<template>
  <div class="series-list">
    <div
      v-for="group in seriesGroups"
      :key="group.series.key"
      class="series-group"
      :style = "{ maxHeight: collapseMap[group.series.key] ? '40px' : '100%' }"
    > 
      <div style="display: flex;">
        <button title="Collapse series" class="collapse-btn material-symbols-outlined" @click="collapseMap[group.series.key] = !collapseMap[group.series.key]">{{ collapseMap[group.series.key] ? 'keyboard_arrow_down' : 'keyboard_arrow_up' }}</button>
        <h3 class="series-name">{{ group.series.name }}</h3>
        <button v-if="!showCleanup" title="Attempt to clean Book titles of remnants from series" class="ctrl-btn material-symbols-outlined" @click="showCleanup = true">cleaning_services</button>
        <div v-else style="display: flex;">
          <input  class="series-clean" v-model="cleanStr" @keyup.enter="$emit('cleanupSeries', group.series.key, cleanStr)" type="text" placeholder="alternative Series title" />
          <button class="ctrl-btn material-symbols-outlined" @click="showCleanup = false">arrow_right</button>
        </div>
        <button title="Include other-author books of this series" class="ctrl-btn material-symbols-outlined" @click="$emit('completeSeries', group.series.key)">matter</button>
        <button title="Download every book of series" class="ctrl-btn material-symbols-outlined" @click="$emit('downloadSeries', group.series.key)">download</button>
        <button title="Delete entire Series from database" class="ctrl-btn material-symbols-outlined" @click="$emit('deleteSeries', group.series.key)">delete</button>
      </div>
      <div class="book-list">
        <BookItem
          v-for="book in group.books"
          :key="book.key"
          :book="book"
          @downloadBook="$emit('downloadBook', $event)"
          @deleteBook="$emit('deleteBook', $event)"
          @editBook="$emit('editBook', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { api } from '@/main.ts'
import BookItem from '@/components/BookItem.vue'

interface Series {
  autor_key: string
  key: string
  name: string
}

interface Book {
  key: string
  name: string
  autor_key: string
  bild?: string
  reihe_key?: string
  reihe_position?: number
  a_dl_loc?: string
  b_dl_loc?: string
}

const route = useRoute()

const collapseMap = ref<Record<string, boolean>>({})
const seriesGroups = ref<Array<{ series: Series; books: Book[] }>>([])
const showCleanup = ref(false)
const cleanStr = ref<string>('')

onMounted(async () => {
  try {
    const { data: seriesList } = await api.get<Series[]>(`/author/${route.params.key}/series`)
    const groups = await Promise.all(
      seriesList.map(async (s: Series) => {
        const { data: books } = await api.get<Book[]>(`/series/${s.key}/books`)
        books.sort((a: Book, b: Book) => (a.reihe_position ?? 0) - (b.reihe_position ?? 0))
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
  overflow: hidden;
}

.ctrl-btn{
  color: var(--lightGray);
  padding: 0px 8px;
  color: #fff;
  margin: 10px 2px;
}

.series-clean{
  margin: 10px 2px;
}

.series-name {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 10px 0;
  flex-grow: 1;
}

.book-list {
  display: table;
  border-collapse: separate;   /* allow border-spacing */
  border-spacing: 0 8px;       /* vertical gutter between rows */
}

.collapse-btn{
  color: var(--lightGray);
  background-color: transparent;
  margin-right: 10px;
  margin-bottom: 5px;
}
</style>
