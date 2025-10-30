<template>
  <div class="book-item">
    <div class="checkbox">
      <input type="checkbox" class="selector" :checked="checked" @click="emit('checkboxClick', { event: $event as MouseEvent, key: book.key })"/>
    </div>
    <img class="book-icon" :src="book.bild" :alt="book.name" />
    <div class="book-name">
      <router-link class="name-text" :to="`/book/${book.key}`">{{ book.name }}</router-link>
    </div>
    <div class="info">
      {{ book.key }}
    </div>
    <div class="info">
      {{ book.reihe_position?? "" }}
    </div>
    <div class="info material-symbols-outlined" :title="getTooltip()">
      {{ getStatus() }}
    </div>
    <div class="book-download">
      <button class="material-symbols-outlined" @click="emit('editBook', props.book)">edit</button>
      <button class="material-symbols-outlined" @click="emit('downloadBook', [props.book.key])">download</button>
      <button class="material-symbols-outlined" @click="emit('searchBook', props.book.key)">quick_reference_all</button>
      <button class="material-symbols-outlined" @click="emit('deleteBook', [props.book.key])">delete</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Book } from '@/main.ts'


const props = defineProps<{
  book: Book
  showBox: boolean
  checked?: boolean
  audio: boolean
}>()
const emit = defineEmits<{
  (e: 'checkboxClick', payload: { event: MouseEvent; key: string }): void
  (e: 'downloadBook', key: string[]): void
  (e: 'searchBook', key: string): void
  (e: 'deleteBook', keys: string[]): void
  (e: 'editBook', book: Book): void
}>()

function getStatus() {
  const acts = props.book.activities.filter((act) => act.audio === props.audio)
  if (acts.some(a => a.status.includes('download'))) {
    return 'cloud_download'
  }
  if (acts.some(a => a.status === 'failed')) {
    return 'error'
  }
  if (acts.some(a => a.status === 'imported')) {
    return 'cloud_done'
  }
  return 'cloud_off'
}
function getTooltip() {
  const acts = props.book.activities.filter((act) => act.audio === props.audio)
  if (acts.some(a => a.status.includes('download'))) {
    return 'Downloading'
  }
  if (acts.some(a => a.status === 'imported')) {
    return 'Imported'
  }
  return 'Not downloaded'
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
  max-height: 50px;
}

.book-name{
  display: flex;
  align-items: center;
  width: 30%;
  margin: 0 20px;
  overflow: hidden; 
  text-overflow: ellipsis;
}
.info{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20%;
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

.name-text{
  white-space: nowrap;          /* prevents line breaks */
}

.checkbox{
  width: 50px;
  min-width: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
