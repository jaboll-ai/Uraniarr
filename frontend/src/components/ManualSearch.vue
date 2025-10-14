<template>
  <div v-if="visible" class="overlay" @click.self="close">
    <div class="modal">
      <h2 class="modal-title">{{ query }}</h2>
      <div class="table-wrapper">
        <table class="version-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>GUID</th>
              <th>Size</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="file in versions" :key="file.guid">
              <td class="title">{{ file.name }}</td>
              <td class="guid">{{ file.guid }}</td>
              <td>{{ formatSize(file.size) }}</td>
              <td>
                <button class="download-btn material-symbols-outlined" @click="choose(file)">
                  Download
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="actions">
        <div class="pagination">
          <div>
            <button :disabled="page == 0" class="arrow-btn material-symbols-outlined" @click="paginate(page-1)" >arrow_back_ios</button>
            <button :disabled="page == pages-1" class="arrow-btn material-symbols-outlined" @click="paginate(page+1)">arrow_forward_ios</button>
          </div>
          <span style="text-align: center;">{{ page+1 }} / {{ pages }}</span>
        </div>
        <div style="flex-grow: 1;"></div>
        <div style="justify-content: end;">
          <button class="btns material-symbols-outlined" @click="close">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface BookNzb {
  name: string
  guid: string
  size: string | number
}

const props = defineProps<{
  versions: BookNzb[]
  visible: boolean
  query: string
  book: string
  pages: number
}>()

var page = ref(0)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', key: string, file: BookNzb): void
  (e: 'paginate', key: string, page: number): void
}>()

function close() {
  emit('close')
  page.value = 0
}

function choose(file: BookNzb) {
  emit('select', props.book, file)
}

function formatSize(size: string | number) {
  const num = Number(size)
  if (isNaN(num)) return size
  if (num < 1024) return `${num} B`
  if (num < 1024 ** 2) return `${(num / 1024).toFixed(1)} KB`
  if (num < 1024 ** 3) return `${(num / 1024 ** 2).toFixed(1)} MB`
  return `${(num / 1024 ** 3).toFixed(1)} GB`
}

async function paginate(p: number) {
  page.value = Math.min(Math.max(p, 0), props.pages-1)
  emit('paginate', props.book, page.value)
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--backgroundWhite);
  padding: 20px;
  border-radius: 12px;
  width: 80%;
  max-width: 700px;
  box-shadow: 0 5px 25px rgba(0,0,0,0.2);
}

.modal-title {
  margin: 0;
  text-align: center;
}

.version-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

.version-table th,
.version-table td {
  border-bottom: 1px solid var(--offWhite);
  padding: 8px;
  text-align: left;
}

.version-table th {
  background: var(--offWhite);
  font-weight: bold;
}

.guid {
  font-family: monospace;
  color: #666;
}

.download-btn {
  padding: 8px 8px;
}

.actions {
  display: flex;
  justify-content: flex-end;
}


.title{
    word-wrap: anywhere;
}

.arrow-btn {
    background: none;
    padding: 8px;
    color: var(--mainColor);
}
.arrow-btn:hover {
    color: var(--fontColor);
}
.table-wrapper {
  max-height: 400px;
  padding: 0 7px;
  overflow-y: auto;
  display: block;
  margin: 12px 0;
}
.btns{
  padding: 8px;
  margin-right: 15px;
}

.pagination{
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style>
