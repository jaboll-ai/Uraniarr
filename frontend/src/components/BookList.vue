<template>
  <!-- <button title="Select" class="ctrl-btn material-symbols-outlined" @click="showBox = !showBox">check_box</button> -->
  <div class="group">
    <div class="book-list">
      <BookItem
        v-for="(book, index) in books"
        :key="book.key"
        :book="book"
        :showBox="showBox"
        :checked="selected.includes(book.key)"
        @checkboxClick="onCheckboxClick($event, index)"
        @downloadBook="$emit('downloadBook', $event)"
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
  margin: 10px 0;
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