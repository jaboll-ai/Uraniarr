<template>
  <div class="book-item">
    <div class="checkbox">
      <input type="checkbox" class="selector" :checked="checked" @click="emit('checkboxClick', { event: $event as MouseEvent, key: book.key })"/>
    </div>
    <img class="book-icon" :src="book.bild" :alt="book.name" />
    <div class="info">
      <a :href="`/book/${book.key}`">{{ book.name }}</a>
    </div>
    <div class="info">
      {{ book.key }}
    </div>
    <div class="info">
      {{ book.reihe_position?? "" }}
    </div>
    <div class="book-download">
      <button class="material-symbols-outlined" @click="showEditor = true">edit</button>
      <button class="material-symbols-outlined" @click="emit('downloadBook', [props.book.key])">download</button>
      <button class="material-symbols-outlined" @click="emit('searchBook', props.book.key)">quick_reference_all</button>
      <button class="material-symbols-outlined" @click="emit('deleteBook', [props.book.key])">delete</button>
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
import type { Book } from '@/main.ts'


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
.book-icon {
  width: 50px;
  height: 50px;
  aspect-ratio: 1 / 1;
  object-fit: cover;
}

.book-item{
  display: flex;
  background-color: var(--backgroundWhite);
  border-radius: 8px;
}

.info{
  display: flex;
  align-items: center;
  width: 25%;
  margin: 0 20px;
}
.book-download{
  display: flex;
  justify-content: flex-end;
  flex-grow: 1;
  margin: 0 10px;
}

.selector {
  transform: scale(1.2);/* translateY(10px) translateX(5px); */
  margin: 0;
}

.checkbox{
  width: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
