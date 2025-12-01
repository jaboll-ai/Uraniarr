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
        <div class="series-name">
          <div class="name-container">
            <span v-if="!showEditSeriesMap[group.series.key]">
              {{ group.series.name }}
            </span>
            <input v-else type="text" v-model="newNameSeries"
              @keyup.enter="emit('editSeries',  group.series.key, { name: newNameSeries }); showEditSeriesMap[group.series.key] = false"
              @keyup.esc="newNameSeries = ''; showEditSeriesMap[group.series.key] = false"
            />
            <button v-if="!showEditSeriesMap[group.series.key]" class="edit-btn material-symbols-outlined"
              @click="showEditSeriesMap[group.series.key] = true; newNameSeries = group.series.name;" title="Edit the series name"
            >edit</button>
          </div>
          <span class="series-id">({{ group.series.key }})</span>
        </div>
        <button v-if="!showCleanup[group.series.key]" title="Attempt to clean Book titles of remnants from series" class="ctrl-btn material-symbols-outlined" @click="showCleanup[group.series.key] = true">cleaning_services</button>
        <div v-else style="display: flex;">
          <input class="series-clean" @keyup.enter="$emit('cleanupSeries', group.series.key, ($event.target as HTMLInputElement).value)" type="text" placeholder="alternative Series title" :key="group.series.key"/>
          <button class="ctrl-btn material-symbols-outlined" @click="showCleanup[group.series.key] = false">arrow_right</button>
        </div>
        <button title="Join Series" class="ctrl-btn material-symbols-outlined" @click="openSelector(group.series.key)">join</button>
        <button title="Complete series (use if missing)" class="ctrl-btn material-symbols-outlined" @click="$emit('completeSeries', group.series.key)">matter</button>
        <LoadingButton title="Download every book of series" class="ctrl-btn" :loading="loadingEntities[group.series.key]?.download === 'loading'"
          :text="loadingEntities[group.series.key]?.download ?? 'download'"
          @click="$emit('downloadSeries', group.series.key)"/>
        <button title="Delete entire series from database" class="ctrl-btn material-symbols-outlined" @click="$emit('deleteSeries', group.series.key)">delete</button>
      </div>
      <BookList
      @downloadBook="$emit('downloadBook', $event)"
      @deleteBook="$emit('deleteBook', $event)"
      @editBook="$emit('editBook', $event)"
      @searchBook="$emit('searchBook', $event)"
      :showBox="showBox" :books="group.books" :seriesGroups="[]"
      :audio="audio"/>
    </div>
  </div>

  <SeriesUnionSelector
    :items="items"
    :seriesID="seriesID"
    :visible="showSelector"
    @close="closeSelector"
    @unite="emitUniteSeries"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SeriesUnionSelector from '@/components/SeriesUnionModal.vue'
import BookList from './BookList.vue'
import LoadingButton from './LoadingButton.vue'
import { loadingEntities } from '@/utils'
import type { Book, Series } from '@/main.ts'


const props = defineProps<{
  books: Book[] //throw away
  showBox: boolean
  seriesGroups: Array<{ series: Series; books: Book[] }>
  audio: boolean
}>()
const emit = defineEmits<{
  (e: 'downloadBook', key: string[]): void
  (e: 'searchBook', key: string): void
  (e: 'completeSeries', key: string): void
  (e: 'downloadSeries', key: string): void
  (e: 'deleteSeries', key: string): void
  (e: 'deleteBook', keys: string[]): void
  (e: 'uniteSeries', keys: { series_id: string; series_ids: string[] }): void
  (e: 'editSeries', key: string, payload: {}): void
  (e: 'editBook', book: Book): void
  (e: 'cleanupSeries', key: string, name: string): void
}>()

const collapseMap = ref<Record<string, boolean>>({})
const showEditSeriesMap = ref<Record<string, boolean>>({})
const showCleanup = ref<Record<string, boolean | undefined>>({})
const showBox = ref(false)

const seriesID = ref()
const showSelector = ref(false)
const items = ref<Series[]>([])
const newNameSeries = ref("")

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
  padding: 0px 8px;
  margin: 10px 2px;
}

.series-clean{
  margin: 10px 2px;
}

.series-name {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 10px 10px;
  flex-grow: 1;
}

.name-container:hover .edit-btn{
  display: block;
}

.edit-btn{
  font-size: 12pt;
  margin: 0 6px;
  display: none;
}

.name-container{
  display: flex;
  align-items: center
}

.series-id{
  font-size: 0.85rem;
  color: gray;
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
  margin: 10px 0;
}
</style>
