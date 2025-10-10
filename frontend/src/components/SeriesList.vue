<template>
  <div class="series-list">
    <div
      v-for="group in seriesGroups"
      :key="group.series.key"
      class="series-group"
      :style="{ maxHeight: collapseMap[group.series.key] ? '100%' : '40px' }"
    > 
      <div style="display: flex;">
        <button title="Collapse series" class="collapse-btn material-symbols-outlined" @click="collapseMap[group.series.key] = !collapseMap[group.series.key]">
          {{ collapseMap[group.series.key] ? 'keyboard_arrow_up' : 'keyboard_arrow_down' }}
        </button>
        <h3 class="series-name">{{ group.series.name }}</h3>
        <button v-if="!showCleanup" title="Attempt to clean Book titles of remnants from series" class="ctrl-btn material-symbols-outlined" @click="showCleanup = true">cleaning_services</button>
        <div v-else style="display: flex;">
          <input class="series-clean" @keyup.enter="$emit('cleanupSeries', group.series.key, ($event.target as HTMLInputElement).value)" type="text" placeholder="alternative Series title" :key="group.series.key"/>
          <button class="ctrl-btn material-symbols-outlined" @click="showCleanup = false">arrow_right</button>
        </div>
        <button title="Join Series" class="ctrl-btn material-symbols-outlined" @click="openSelector(group.series.key)">join</button>
        <button title="Include other-author books of this series" class="ctrl-btn material-symbols-outlined" @click="$emit('completeSeries', group.series.key)">matter</button>
        <button title="Download every book of series" class="ctrl-btn material-symbols-outlined" @click="$emit('downloadSeries', group.series.key)">download</button>
        <button title="Delete entire Series from database" class="ctrl-btn material-symbols-outlined" @click="$emit('deleteSeries', group.series.key)">delete</button>
      </div>
      <BookList @downloadBook="$emit('downloadBook', $event)" @deleteBook="$emit('deleteBook', $event)" @editBook="$emit('editBook', $event)" :showBox="showBox" :books="group.books" :seriesGroups="[]"/>
    </div>
  </div>

  <SeriesUnionSelector
    v-if="showSelector"
    :items="items"
    :seriesID="seriesID"
    @close="closeSelector"
    @unite="emitUniteSeries"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SeriesUnionSelector from '@/components/SeriesUnionModal.vue'
import BookList from './BookList.vue'
const props = defineProps<{
  books: Book[] //throw away
  showBox: boolean
  seriesGroups: Array<{ series: Series; books: Book[] }>
}>()
const emit = defineEmits<{
  (e: 'downloadBook', key: string): void
  (e: 'completeSeries', key: string): void
  (e: 'downloadSeries', key: string): void
  (e: 'deleteSeries', key: string): void
  (e: 'deleteBook', keys: string[]): void
  (e: 'uniteSeries', keys: { series_id: string; series_ids: string[] }): void
  (e: 'editBook', book: Book): void
  (e: 'cleanupSeries', key: string, name: string): void
}>()

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

const collapseMap = ref<Record<string, boolean>>({})
const showCleanup = ref(false)
const showBox = ref(false)

const seriesID = ref()
const showSelector = ref(false)
const items = ref<Series[]>([])


function emitUniteSeries(selected: string[]) {
  emit('uniteSeries', { series_id: seriesID.value, series_ids: selected })
  closeSelector()
}

function closeSelector() {
  seriesID.value = null
  showSelector.value = false
}

function openSelector(id: string) {
  seriesID.value = id
  showSelector.value = true

  const filteredItems = props.seriesGroups.reduce((acc, curr) => {
    if (curr.series.key !== id) {
      acc.push(curr.series)
    }
    return acc
  }, [] as Series[])
  items.value = filteredItems
}

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

.group{
  border:none;
  background-color: transparent;
  padding: 0;
  margin: 0;
}

.collapse-btn{
  color: var(--lightGray);
  background-color: transparent;
  margin-right: 10px;
  margin-bottom: 5px;
}
</style>
