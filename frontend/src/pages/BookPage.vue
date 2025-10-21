<template>
  <div class="book-page">
    <div class="book-header">
      <img v-if="book?.bild" :src="book.bild" :alt="book.name" class="book-image" />
      <div v-else class="book-placeholder">{{ getInitials(book?.name || '') }}</div>

      <div class="book-info">
        <h2 class="book-name">{{ book?.name }}</h2>
        <p class="book-meta">
          <span><strong>Author:</strong> {{ authorName || 'Unknown' }}</span><br />
          <span><strong>Series Position:</strong> {{ book?.reihe_position ?? '-' }}</span>
        </p>

        <div class="actions">
        <button class="material-symbols-outlined" @click="showEditor = true">edit</button>
          <button class="ctrl-btn material-symbols-outlined" @click="downloadBook(book?.key)">download</button>
          <button class="ctrl-btn material-symbols-outlined" @click="showConfirmDelete = true">delete</button>
          <button class="ctrl-btn material-symbols-outlined" @click="searchBook(book?.key || '')">quick_reference_all</button>
        </div>
      </div>
    </div>

    <div class="book-act-container">
      <div class="book-activities">
        <h3>Audio activities</h3>
        <div v-for="act in book?.activities?.filter(a => a.audio)" :key="act.nzo_id" class="activity-item">
          <div class="activity-title">{{ act.release_title }}</div>
          <div class="activity-status">
            Status: <span :class="act.status">{{ act.status }}</span>
          </div>
        </div>
      </div>
      <div class="book-activities">
        <h3>Book activities</h3>
        <div v-for="act in book?.activities?.filter(a => !a.audio)" :key="act.nzo_id" class="activity-item">
          <div class="activity-title">{{ act.release_title }}</div>
          <div class="activity-status">
            Status: <span :class="act.status">{{ act.status }}</span>
          </div>
        </div>
      </div>
    </div>
    <ConfirmModal
      :visible="showConfirmDelete"
      message="Are you sure you want to delete this book?"
      @confirm="deleteBook"
      @cancel="showConfirmDelete = false"
    />
    <EditModal v-if="book"
      :visible="showEditor"
      :book="book"
      @close="showEditor = false"
      @editBook="editBook"
    />
    <ManualSearch :query="query" :visible="interactiveSearch" :book="manualSearchKey" 
    :pages="manualSearchPages" :versions="manualSearchVersions"
     @close="closeManualSearch" @select="downloadBookManual" @paginate="searchBookPaginate"/>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api, dapi } from '@/main.ts'
import ConfirmModal from '@/components/ConfirmModal.vue'
import EditModal from '@/components/EditModal.vue'
import ManualSearch from '@/components/ManualSearch.vue'
import { getInitials } from '@/utils.ts'
import { useRoute } from 'vue-router'
import type { BookNzb, Book, InteractiveSearch } from '@/main.ts'


const route = useRoute()
const book = ref<Book>()
const authorName = ref('')
const showConfirmDelete = ref(false)
const showEditor = ref(false)
const interactiveSearch = ref(false)
const manualSearchVersions = ref<BookNzb[]>([])
const query = ref("")
const manualSearchKey = ref("")
const manualSearchPages = ref(0)
const timer = ref<number | null>(null)


async function editBook(book: Book) {
  try {
    await api.patch(`/book/${book.key}`, book)
  } catch (err) {
    console.error('Failed to edit book', err)
  }
}

onMounted(async () => {
  await fetchBook()
  timer.value = window.setInterval(fetchBook, 10_000)
})

onBeforeUnmount(() => {
  if (timer.value) clearInterval(timer.value)
})

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

async function downloadBook(key?: string) {
  if (!key) return
  try {
    await dapi.post(`/book/${key}`)
  } catch (err) {
    console.error('Failed to download book:', err)
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

async function searchBook(key: string) {
  await searchBookPaginate(key, 0)
}

async function searchBookPaginate(key: string, page: number) {
  try {
    interactiveSearch.value = true
    const response = await dapi.get<InteractiveSearch>(`/manual/${key}`, { params: { page: page } })
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

async function downloadBookManual(key: string, nzb: BookNzb) {
  try {
    await dapi.post('/guid', {book_key : key, guid : nzb.guid, name : nzb.name})
  } catch (err) {
    console.error('Failed to download book', err)
  }
}
</script>

<style scoped>
.book-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.book-header {
  display: flex;
  gap: 16px;
  padding: 10px;
  background-color: var(--offWhite);
  border-radius: 10px;
  align-items: center;
}

.book-image {
  width: 190px;
  border-radius: 8px;
  aspect-ratio: 1/1;
  object-fit: cover;
}

.book-placeholder {
  width: 190px;
  height: 190px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ccc;
  color: #fff;
  font-weight: bold;
  border-radius: 8px;
}

.book-info {
  flex: 1;
}

.book-name {
  margin: 0;
  font-size: 1.6rem;
}

.book-meta {
  color: var(--fontColor);
  margin: 0.4rem 0;
}

.actions {
  margin-top: 0.5rem;
}

.ctrl-btn {
  padding: 0px 8px;
  margin: 10px 2px;
}

.book-act-container {
  display: flex;
  flex-direction: row;
  gap: 20px;
}

.book-activities {
  flex-grow: 1;
  background: var(--backgroundWhite);
  border-radius: 8px;
  padding: 10px;
  background-color: var(--offWhite);
}

.activity-item {
  border-top: 1px solid var(--borderColor);
  padding: 6px 0;
}

.activity-title {
  font-weight: 600;
}

.activity-status .download {
  color: #27ae60;
}
.activity-status .imported {
  color: var(--mainColor); 
}
.activity-status .canceled {
  color: #7f8c8d;
}
.activity-status .failed {
  color: #e74c3c;
}
.activity-status .overwritten {
  color: #f39c12;
}


@media (max-width: 600px) {
  .book-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .book-image,
  .book-placeholder {
    width: 100%;
    max-width: 250px;
  }

  .book-act-container {
    flex-direction: column;
  }
}
</style>
