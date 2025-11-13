<template>
  <div class="book-page">
    <div class="book-header">
      <div class="book-cover">
        <img
          v-if="book?.bild"
          :src="book.bild"
          :alt="book.name"
          class="cover-image"
        />
        <div v-else class="cover-placeholder">
          {{ getInitials(book?.name || '') }}
        </div>
      </div>

      <div class="book-details">
        <h2 class="book-title">{{ book?.name }}</h2>
        <div class="book-meta">
          <p><strong>Author:</strong> {{ authorName || 'Unknown' }}</p>
          <p><strong>Series Position:</strong> {{ book?.position ?? '-' }}</p>
        </div>

        <div class="book-actions" v-if ="book">
          <button class="ctrl-btn material-symbols-outlined" @click="showEditor = true">edit</button>
          <button class="ctrl-btn material-symbols-outlined" @click="downloadBook([book.key])">download</button>
          <button class="ctrl-btn material-symbols-outlined" @click="showConfirmDelete = true">delete</button>
          <button class="ctrl-btn material-symbols-outlined" @click="searchBook(book.key)">quick_reference_all</button>
          <button class="ctrl-btn material-symbols-outlined" @click="previewRetagBook(book.key)">graph_1</button>
          <button class="ctrl-btn material-symbols-outlined"
          @click="animate" :title="`Toggle to ${audio ? 'book' : 'audiobooks'}`"
          :class="{ anim: isAnimating }" @animationend="isAnimating = false">{{ audio ? "headphones" : "book" }}</button>
        </div>
      </div>
    </div>
    <div class="book-section">
      <div class="file-group">
        <h3>Audio Files</h3>
        <div v-for="file in files.audio" :key="file.path" class="file-row">
          <span class="file-path">{{ file.path }}</span>
          <span class="file-size">{{ formatSize(file.size) }}</span>
        </div>
      </div>

      <div class="file-group">
        <h3>Book Files</h3>
        <div v-for="file in files.book" :key="file.path" class="file-row">
          <span class="file-path">{{ file.path }}</span>
          <span class="file-size">{{ formatSize(file.size) }}</span>
        </div>
      </div>
    </div>
    <div class="book-section">
      <div class="activity-group">
        <h3>Audio Activities</h3>
        <div
          v-for="act in book?.activities?.filter(a => a.audio)"
          :key="act.nzo_id"
          class="activity-row"
        >
          <div class="activity-info">
            <div class="activity-title">{{ act.release_title }}</div>
            <div class="activity-status">
              Status: <span :class="['status', act.status]">{{ act.status }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="activity-group">
        <h3>Book Activities</h3>
        <div
          v-for="act in book?.activities?.filter(a => !a.audio)"
          :key="act.nzo_id"
          class="activity-row"
        >
          <div class="activity-info">
            <div class="activity-title">{{ act.release_title }}</div>
            <div class="activity-status">
              Status: <span :class="['status', act.status]">{{ act.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODALS -->
    <ConfirmModal
      :visible="showConfirmDelete"
      message="Are you sure you want to delete this book?"
      @confirm="deleteBook"
      @cancel="showConfirmDelete = false"
    />

    <EditModal
      v-if="book"
      :visible="showEditor"
      :book="book"
      @close="showEditor = false"
      @editBook="editBook"
    />

    <RetagModal v-if="prv"
      :visible="showRetag"
      :prv="prv"
      @retagBook="retagBooks"
      @cancel="showRetag = false"
    />

    <ManualSearch
      :query="query"
      :visible="interactiveSearch"
      :book="manualSearchKey"
      :pages="manualSearchPages"
      :versions="manualSearchVersions"
      @close="closeManualSearch"
      @select="downloadBookManual"
      @paginate="searchBookPaginate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api, dapi } from '@/main.ts'
import ConfirmModal from '@/components/ConfirmModal.vue'
import EditModal from '@/components/EditModal.vue'
import ManualSearch from '@/components/ManualSearch.vue'
import { getInitials, formatSize } from '@/utils.ts'
import { useRoute } from 'vue-router'
import type { BookNzb, Book, InteractiveSearch, PreviewRetag } from '@/main.ts'
import RetagModal from '@/components/RetagBookModal.vue'


const route = useRoute()
const book = ref<Book>()
const authorName = ref('')
const showConfirmDelete = ref(false)
const showEditor = ref(false)
const showRetag = ref(false)
const interactiveSearch = ref(false)
const manualSearchVersions = ref<BookNzb[]>([])
const query = ref("")
const manualSearchKey = ref("")
const manualSearchPages = ref(0)
const timer = ref<number | null>(null)
const files = ref<{ audio: { path: string; size: number }[]; book: { path: string; size: number }[] }>({
  audio: [],
  book: [],
})
const audio = ref(true)
const isAnimating = ref(false);
const prv = ref<PreviewRetag>()

async function editBook(book: Book) {
  try {
    const { key, ...data } = book
    await api.patch(`/book/${key}`, data)
  } catch (err) {
    console.error('Failed to edit book', err)
  }
  fetchInfo()
}

onMounted(async () => {
  await fetchInfo()
  timer.value = window.setInterval(fetchInfo, 10_000)
})

onBeforeUnmount(() => {
  if (timer.value) clearInterval(timer.value)
})

async function fetchInfo(){
  fetchBook()
  fetchFiles()
}

async function fetchFiles() {
  try {
    const { data } = await api.get(`/book/files/${route.params.key}`)
    files.value = data
  } catch (err) {
    console.error('Failed to fetch files:', err)
  }
}

async function fetchBook() {
  try {
    const { data } = await api.get<Book>(`/book/${route.params.key}`)
    book.value = data
    const author = await api.get<{ name: string }>(`/author/${data.autor_key}`)
    authorName.value = author.data.name
  } catch (err) {
    console.error('Failed to fetch book:', err)
  }
}

async function downloadBook(keys: string[]) {
  try {
    for (const key of keys) {
      await dapi.post(`/book/${key}`, null, { params: { audio : audio.value } })
    }
  } catch (err) {
    console.error('Failed to download book', err)
  }
}

async function downloadBookManual(key: string, nzb: BookNzb) {
  try {
    await dapi.post('/guid', {book_key : key, guid : nzb.guid, download : nzb.download, name : nzb.name}, { params: { audio : audio.value } })
  } catch (err) {
    console.error('Failed to download book', err)
  }
}

async function deleteBook() {
  if (!book.value?.key) return
  try {
    await api.delete(`/book/${book.value.key}`)
    showConfirmDelete.value = false
  } catch (err) {
    console.error('Failed to delete book:', err)
  }
}

async function previewRetagBook(key: string) {
  try {
    showRetag.value = true
    const response = await api.get<PreviewRetag>(`/retag/book/${key}`)
    prv.value = response.data
  } catch(err){
    console.log(err)
  }
}

async function retagBooks(keys: string[]) {
  console.log(keys)
  showRetag.value = false
  try {
    await api.post(`/retag/books`, keys)
  } catch (err) {
    console.error('Failed to retag author', err)
  }
  fetchBook()
}

async function searchBook(key: string) {
  await searchBookPaginate(key, 0)
}
async function searchBookPaginate(key: string, page: number) {
  try {
    interactiveSearch.value = true
    const response = await dapi.get<InteractiveSearch>(`/manual/${key}`, { params: { page: page, audio: audio.value } })
    manualSearchVersions.value = response.data.nzbs
    query.value = response.data.query
    manualSearchPages.value = response.data.pages
    manualSearchKey.value = key
  } catch(err){
    console.log(err)
    interactiveSearch.value = true
  }
}

async function closeManualSearch() {
  interactiveSearch.value = false
    manualSearchVersions.value = []
    query.value = ""
    manualSearchKey.value = ""
}

async function animate() {
  audio.value = !audio.value
  if (audio.value) {
    document.documentElement.style.removeProperty('--mainColor');
  } else {
    document.documentElement.style.setProperty('--mainColor', '#be8e8e');
  }
  if (!isAnimating.value) {
    isAnimating.value = true;
  }
}
</script>

<style scoped>
/* Layout Containers */
.book-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.5rem;
  flex: 1;
}

/* Header */
.book-header {
  display: flex;
  flex-wrap: wrap;
  gap: 1.2rem;
  background: var(--offWhite);
  border-radius: 12px;
  padding: 1rem;
  align-items: flex-start;
}

.book-cover {
  flex-shrink: 0;
}

.cover-image,
.cover-placeholder {
  width: 180px;
  height: 180px;
  border-radius: 8px;
  object-fit: cover;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  background: #ccc;
  color: white;
}

/* Details */
.book-details {
  flex: 1;
  min-width: 250px;
}

.book-title {
  margin: 0;
  font-size: 1.6rem;
  line-height: 1.3;
  word-wrap: break-word;
}

.book-meta {
  margin: 0.5rem 0;
  color: var(--fontColor);
}

.book-meta p {
  margin: 0.2rem 0;
}

.icon-btn:hover {
  background: var(--mainColorHover, #ddd);
}

/* Sections */
.book-section {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.file-group,
.activity-group {
  flex: 1 1 45%;
  background: var(--offWhite);
  border-radius: 10px;
  padding: 0.8rem;
  min-width: 280px;
}

/* Files */
.file-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--borderColor);
  padding: 0.4rem 0;
  gap: 0.5rem;
}

.file-path {
  flex: 1;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: rtl;
  text-align: left;
}

.file-size {
  white-space: nowrap;
  font-size: 0.9rem;
}

/* Activities */
.activity-row {
  border-top: 1px solid var(--borderColor);
  padding: 0.5rem 0;
}

.activity-title {
  font-weight: 600;
  word-wrap: break-word;
}

.status.download {
  color: #27ae60;
}
.status.imported {
  color: var(--mainColor);
}
.status.canceled {
  color: #7f8c8d;
}
.status.failed {
  color: #e74c3c;
}
.status.overwritten {
  color: #f39c12;
}
.ctrl-btn{
  width: 35px;
  height: 50px;
  transition: transform 0.2s ease;
}
.ctrl-btn.anim {
  animation: growAndTilt 0.35s ease forwards;
}

/* Responsive */
@media (max-width: 700px) {
  .book-section {
    flex-direction: column;
    flex-wrap: nowrap;
    /* max-width: 500px; */
  }

  /* .book-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .book-details {
    width: 100%;
  }

  .cover-image,
  .cover-placeholder {
    width: 100%;
    max-width: 250px;
  } */
}
</style>