<template>
  <div class="download-list">
    <div v-for="item in downloads" :key="item.book_key" class="download-item">
      <div class="header">
        <div class="title">{{ item.book_name }}</div>
        <div class="status">{{ item.status }}</div>
      </div>

      <div class="filename">{{ item.filename }}</div>

      <div class="progress-bar">
        <div class="progress" :style="{ width: item.percentage + '%' }"></div>
      </div>

      <div class="footer">
        <span>{{ item.percentage }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { dapi } from '@/main'

interface DownloadItem {
  percentage: string
  filename: string
  book_key: string
  book_name: string
  status: string
}

const downloads = ref<DownloadItem[]>([])

const timer = ref<number | null>(null)

onMounted(async () => {
  await fetchQueue()
  timer.value = window.setInterval(fetchQueue, 10_000)
})

onBeforeUnmount(() => {
  if (timer.value) clearInterval(timer.value)
})

async function fetchQueue() {
  try {
    const response = await dapi.get<DownloadItem[]>("/activities")
    downloads.value = response.data
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
}
</script>

<style scoped>
.download-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: var(--offWhite);
  border-radius: 10px;
  flex-grow: 1;
}

.download-item {
  background: var(--backgroundWhite);
  border: 1px solid var(--borderColor);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
}

.filename {
  font-size: 0.85rem;
  color: #666;
  margin: 0.3rem 0 0.5rem 0;
  word-break: break-all;
}

.progress-bar {
  height: 8px;
  background: var(--fontColor);
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: var(--mainColor);
  transition: width 0.3s ease;
}

.footer {
  text-align: right;
  font-size: 0.8rem;
  color: var(--fontColor);
  margin-top: 0.4rem;
}
</style>
