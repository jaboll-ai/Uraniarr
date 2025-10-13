<template>
  <div class="book-item">
    <div class="cell">
      <input type="checkbox" class="selector" :checked="checked" @click="emit('checkboxClick', { event: $event as MouseEvent, key: book.key })"/>
    </div>
    <div class="cell">
      <img class="book-icon" :src="book.bild" :alt="book.name" />
    </div>
    <div class="cell book-title">
      <span>{{ book.name }}</span>
    </div>
    <div class="cell book-key">{{ book.key }}</div>
    <div class="cell book-pos">{{ book.reihe_position?? "" }}</div>
    <div class="cell book-download">
      <button class="download-btn material-symbols-outlined" @click="showEditor = true">edit</button>
      <button class="download-btn material-symbols-outlined" @click="emit('downloadBook', [props.book.key])">download</button>
      <button class="download-btn material-symbols-outlined" @click="emit('searchBook', props.book.key)">quick_reference_all</button>
      <button class="download-btn material-symbols-outlined" @click="emit('deleteBook', [props.book.key])">delete</button>
    </div>
  </div>
  <EditModal
      :visible="showEditor"
      :book="book"
      @close="showEditor = false"
      @editBook="editBook"
    />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import EditModal from '@/components/EditModal.vue'
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

const props = defineProps<{
  book: Book
  showBox: boolean
  checked?: boolean
}>()
const emit = defineEmits<{
  (e: 'checkboxClick', payload: { event: MouseEvent; key: string }): void
  (e: 'downloadBook', key: string[]): void
  (e: 'searchBook', key: string): void
  (e: 'deleteBook', keys: string[]): void
  (e: 'editBook', book: Book): void
}>()
const showEditor = ref(false)
function editBook(book: Book) {
  showEditor.value = false
  emit('editBook', book)
}
</script>

<style scoped>
.book-item {
  display: table-row;
}

.cell {
  display: table-cell;
  border-top: 1px solid var(--borderColor);
  border-bottom: 1px solid var(--borderColor);
  background: var(--backgroundWhite);
  padding: 0 10px;
  line-height: 0;
}

.book-item .cell:first-child {
  width: 20px;
  background: none;
  border: none;
}

.book-item .cell:nth-child(2) {
  border-left: 1px solid var(--borderColor);
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
  padding-left: 0;
  width: 40px;
}

.book-item .cell:last-child {
  border-right: 1px solid var(--borderColor);
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

.book-icon {
  width: 50px;
  height: 50px;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}

/* preserve other cell-specific classes */
.book-title,
.book-key,
.book-pos,
.book-download {
  vertical-align: middle;
}

.book-download {
  text-align: right;
}
.download-btn{
  background: none;
  color: var(--lightGray);
}
.download-btn:hover{
  color: var(--mainColor);
}
.book-title {
  overflow: hidden;
  text-overflow: ellipsis;
}

.selector {
  transform: scale(1.2) translateY(-15px);
  margin: 0 5px
}
</style>
