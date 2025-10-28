<template>
  <!-- <button title="Select" class="ctrl-btn material-symbols-outlined" @click="showBox = !showBox">check_box</button> -->
  <div class="group">
    <div class="header">
      <div class="spacer1"></div>
      <div class="name">Name</div>
      <div class="info">Key</div>
      <div class="info">Position</div>
      <div class="info">Status</div>
      <div class="spacer2"></div>
    </div>
    <div class="book-list">
      <BookItem
        v-for="(book, index) in books"
        :key="book.key"
        :book="book"
        :showBox="showBox"
        :checked="selected.includes(book.key)"
        :audio="audio"
        @checkboxClick="onCheckboxClick($event, index)"
        @downloadBook="downloadBook"
        @searchBook="$emit('searchBook', $event)"
        @deleteBook="deleteBook"
        @editBook="$emit('editBook', $event)"
      />
    </div>
  </div>
</template>


<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import BookItem from '@/components/BookItem.vue'
import type { Book } from '@/main.ts'


const props = defineProps<{
  books: Book[]
  showBox: boolean
  seriesGroups: any
  audio: boolean
}>()

const emit = defineEmits<{
  (e: 'downloadBook', key: string[]): void
  (e: 'deleteBook', keys: string[]): void
  (e: 'searchBook', keys: string): void
  (e: 'editBook', book: Book): void
}>()

const selected = ref<string[]>([])
const lastIndex = ref<number | null>(null)

function deleteBook(keys: string[]) {
  if (selected.value.length > 0) {
    emit('deleteBook', selected.value)
  } else {
    emit('deleteBook', keys)
  }
  selected.value = []
}

function downloadBook(keys: string[]) {
  if (selected.value.length > 0) {
    emit('downloadBook', selected.value)
  } else {
    emit('downloadBook', keys)
  }
}

function onCheckboxClick(payload: { event: MouseEvent; key: string }, index: number) {
  const { event, key } = payload
  const checked = (event.target as HTMLInputElement).checked

  if (event.shiftKey && lastIndex.value !== null) {
    const start = Math.min(lastIndex.value, index)
    const end = Math.max(lastIndex.value, index)
    const range = props.books.slice(start, end + 1).map(b => b.key)

    if (checked) {
      selected.value = Array.from(new Set([...selected.value, ...range]))
    } else {
      selected.value = selected.value.filter(k => !range.includes(k))
    }
  } else {
    if (checked) {
      selected.value.push(key)
    } else {
      selected.value = selected.value.filter(k => k !== key)
    }
  }

  lastIndex.value = index
}

function onGlobalDblClick() {
  selected.value = []
}

onMounted(() => {
  window.addEventListener('dblclick', onGlobalDblClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('dblclick', onGlobalDblClick)
})
</script>

<style scoped>
.book-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.spacer1{
  width: 100px;
  min-width: 100px;
}
.spacer2{
  width: 116px;
  min-width: 116px;
}
.name{
  display: flex;
  align-items: center;
  width: 30%;
  margin: 0 20px;
}
.header{
  display: flex;
  flex-direction: row;
  border-radius: 8px;
  color: var(--mainColor);
  margin-top: 10px;
  /* border-bottom: 1px dashed var(--mainColor); */
  font-size: 13pt;
}
.info{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20%;
}
</style>