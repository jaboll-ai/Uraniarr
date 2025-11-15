<template>
  <div class="placeholder" v-if="downloads.length === 0"><span class="symbol material-symbols-outlined">history_toggle_off</span></div>
  <div class="download-list" v-if="downloads.length > 0">
    <div v-for="item in downloads" class="download-item">
      <div class="header">
        <div class="title">
          <router-link :to="{ name: 'Book', params: { key: item.book_key } }">{{ item.book_name }}</router-link>
        </div>
        <div class="status">{{ item.status }}</div>
      </div>

      <div class="filename">{{ item.filename }}</div>
      <div class="progress-container">
        <div class="progress-bar-container">
          <div class="progress-bar">
            <div class="progress" :style="{ width: item.percentage + '%' }"></div>
          </div>
          <div class="footer">
            <span>{{ item.percentage }}%</span>
          </div>
        </div>
        <button class="btn material-symbols-outlined" @click="showCancel = true; downloadId = item.id">close</button>
      </div>
    </div>
    <ConfirmModal
      message="Are you sure you want to cancel this download?"
      :visible="showCancel"
      @confirm="cancelDownload(downloadId)"
      @cancel="showCancel = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { dapi } from '@/main'
import { notify } from "@kyvg/vue3-notification";
import ConfirmModal from '@/components/ConfirmModal.vue'

interface DownloadItem {
  id: string
  percentage: string
  filename: string
  book_key: string
  book_name: string
  status: string
}

const downloads = ref<DownloadItem[]>([])
const showCancel = ref(false)
const downloadId = ref('')

const timer = ref<number | null>(null)

onMounted(async () => {
  await fetchQueue()
  timer.value = window.setInterval(fetchQueue, 10_000)
})

onBeforeUnmount(() => {
  if (timer.value) clearInterval(timer.value)
})

async function cancelDownload(id: string) {
  try {
    await dapi.delete(`/activity/${id}`)
    await fetchQueue()
    showCancel.value = false
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}

async function fetchQueue() {
  try {
    const response = await dapi.get<DownloadItem[]>("/activities")
    downloads.value = response.data
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
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

.progress-container {
  display: flex;
}

.progress-bar-container {
  flex-grow: 1;
}

.btn{
  margin: 0 10px;
}

.progress-bar {
  height: 8px;
  background: var(--fontColor);
  border-radius: 4px;
  overflow: hidden;
  flex-grow: 1;
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

.placeholder{
  display: flex;
  flex-grow: 1;
  justify-content: center;
  align-items: center;
  color: var(--offWhite);
  flex-direction: column;
}
.symbol{
  font-size: 260pt;
}
</style>
