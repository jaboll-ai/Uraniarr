<template>
  <div class="book-item">
    <div class="cell">
      <img class="book-icon" :src="book.bild" :alt="book.name" />
    </div>
    <div class="cell book-title">{{ book.name }}</div>
    <div class="cell book-key">{{ book.key }}</div>
    <div class="cell book-pos">{{ book.reihe_position || "" }}</div>
    <div class="cell book-edit">
      <button class="edit-btn" @click="$emit('downloadBook', props.book.key)">Download</button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Book {
  name: string
  key: string
  autor_key: string
  reihe_key: string | null
  bild: string
  reihe_position: number | null
}

const props = defineProps<{ book: Book }>()

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
  border-left: 1px solid var(--borderColor);
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
  padding-left: 0;
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
.book-edit {
  vertical-align: middle;
}

.book-edit {
  text-align: right;
}
.edit-btn{
  color: var(--lightGray);
  background-color: transparent;
}
</style>
