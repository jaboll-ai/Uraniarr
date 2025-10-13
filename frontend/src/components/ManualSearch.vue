<template>
  <div v-if="visible" class="overlay" @click.self="close">
    <div class="modal">
      <h2 class="modal-title">{{ query }}</h2>

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
              <button class="download-btn" @click="choose(file)">
                Download
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="actions">
        <button class="arrow-btn material-symbols-outlined" @click="">arrow_back_ios</button>
        <button class="arrow-btn material-symbols-outlined">arrow_forward_ios</button>
        <div style="flex-grow: 1;"></div>
        <button class="close-btn" @click="close">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

interface BookNzb {
  name: string
  guid: string
  size: string | number
}

defineProps<{
  versions: BookNzb[]
  visible: boolean
  query: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', file: BookNzb): void
  (e: 'paginate', file: BookNzb): void
}>()

function close() {
  emit('close')
}

function choose(file: BookNzb) {
  emit('select', file)
}

function formatSize(size: string | number) {
  const num = Number(size)
  if (isNaN(num)) return size
  if (num < 1024) return `${num} B`
  if (num < 1024 ** 2) return `${(num / 1024).toFixed(1)} KB`
  if (num < 1024 ** 3) return `${(num / 1024 ** 2).toFixed(1)} MB`
  return `${(num / 1024 ** 3).toFixed(1)} GB`
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
  background: white;
  padding: 20px;
  border-radius: 12px;
  width: 80%;
  max-width: 700px;
  box-shadow: 0 5px 25px rgba(0,0,0,0.2);
}

.modal-title {
  margin: 0 0 12px;
  text-align: center;
}

.version-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

.version-table th,
.version-table td {
  border-bottom: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.version-table th {
  background: #f7f7f7;
  font-weight: bold;
}

.guid {
  font-family: monospace;
  color: #666;
}

.download-btn {
  background-color: var(--mainColor, #2b8a3e);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.download-btn:hover {
  background-color: var(--mainColorDark, #207030);
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.close-btn {
  background: #ccc;
  color: #333;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}
.close-btn:hover {
  background: #bbb;
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
</style>
