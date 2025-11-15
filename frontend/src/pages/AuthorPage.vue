<template>
  <div class="author-page">
    <div class="author-header">
      <div class="author-info">
        <h2 class="author-name">{{ author?.name }}</h2>
        <img v-if="author?.bild" :src="author.bild" :alt="author.name" class="author-image" />
        <div v-else-if="author" class="author-image">{{ getInitials(author.name) }}</div>
        <div class="download-all">
          <LoadingButton class="ctrl-btn" :loading="downloadingAuthor=='throbber'" title="Download every book and audiobook" :text="downloadingAuthor" @click="downloadAuthor"/>
          <LoadingButton class="ctrl-btn" :loading="completingAuthor=='throbber'" title="Try to find missing books"  :text="completingAuthor" @click="completeAuthor"/>
          <button class="ctrl-btn material-symbols-outlined" title="Delete the author from DB" @click="showConfirmAuthor = true">delete</button>
          <button class="ctrl-btn material-symbols-outlined" title="Retag all Books of author" @click="previewRetagAuthor">graph_1</button>
          <button class="ctrl-btn material-symbols-outlined"
          @click="animate" :title="`Toggle to ${audio ? 'book' : 'audiobooks'}`"
          :class="{ active: isAnimating }" @animationend="isAnimating = false">{{ audio ? "headphones" : "book" }}</button>
        </div>
      </div>
      <p class="author-bio">{{ author?.bio }}</p>
    </div>
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        @click="current = tab.name;"
        :class="{ active: current === tab.name }"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="panel">
      <keep-alive>
        <component :is="currentComponent"
          @downloadBook="downloadBook" @completeSeries="completeSeries"
          @downloadSeries="downloadSeries" @deleteSeries="confirmDeleteSeries" @deleteBook="confirmDeleteBook" @editBook="confirmEditBook"
          @cleanupSeries="cleanupSeries" @uniteSeries="uniteSeries" @searchBook="searchBook"
          :showBox="showBox" :books="books" :seriesGroups="seriesGroups" :audio="audio"/>
      </keep-alive>
    </div>
    <ConfirmModal
      :visible="showConfirmAuthor"
      message="Are you sure you want to delete this author?"
      @confirm="deleteAuthor(author?.key)"
      @cancel="showConfirmAuthor = false"
    />
    <ConfirmModal
      :visible="showConfirmBook"
      :message="messageConfirmBook"
      :blocking=true
      @confirm="deleteBook"
      @cancel="showConfirmBook = false"
    />
    <ConfirmModal
      :visible="showConfirmSeries"
      :message="messageConfirmSeries"
      @confirm="deleteSeries"
      @cancel="showConfirmSeries = false"
    />
    <EditModal v-if="editedBook"
      :visible="showEditor"
      :book="editedBook"
      @close="showEditor = false"
      @editBook="editBook"
    />
    <ManualSearch :query="query" :visible="interactiveSearch" :book="manualSearchKey"
    :pages="manualSearchPages" :versions="manualSearchVersions"
     @close="closeManualSearch" @select="downloadBookManual" @paginate="searchBookPaginate"/>
    <RetagAuthorModal v-if="prv"
      :visible="showRetag"
      :author="prv"
      @cancel="showRetag = false"
      @retagBooks="retagBooks"
    />
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import { api, dapi as dapi } from '@/main.ts'
import { getInitials, runBatch } from '@/utils.ts'
import { notify } from '@kyvg/vue3-notification'
import LoadingButton from '@/components/LoadingButton.vue'
import BookList from '@/components/BookList.vue'
import SeriesList from '@/components/SeriesList.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import ManualSearch from '@/components/ManualSearch.vue'
import EditModal from '@/components/EditModal.vue'
import RetagAuthorModal from '@/components/RetagAuthorModal.vue'
import type { Author, BookNzb, Book, Series, InteractiveSearch, RetagAuthor } from '@/main.ts'

const route = useRoute()
const router = useRouter()

const author = ref<Author | null>(null)
const books = ref<Book[]>([])
const showBox = ref(false)
const interactiveSearch = ref(false)
const showConfirmAuthor = ref(false)
const showConfirmBook = ref(false)
const messageConfirmBook = ref("")
const shouldDeleteBooks = ref<string[]>([])
const showConfirmSeries = ref(false)
const showRetag = ref(false)
const prv = ref<RetagAuthor>()
const messageConfirmSeries = ref("")
const shouldDeleteSeries = ref("")
const seriesGroups = ref<Array<{ series: Series; books: Book[] }>>([])
const manualSearchVersions = ref<BookNzb[]>([])
const query = ref("")
const manualSearchKey = ref("")
const manualSearchPages = ref(0)
const downloadingAuthor = ref("download")
const completingAuthor = ref("matter")
const showEditor = ref(false)
const editedBook = ref<Book>()

const timer = ref<number | null>(null)
onMounted(async () => {
  try {
    const response = await api.get<Author>(`/author/${route.params.key}`)
    author.value = response.data
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  fetchBooks()
  timer.value = window.setInterval(fetchBooks, 20_000)
})


onBeforeUnmount(() => {
  if (timer.value) clearInterval(timer.value)
})

const tabs = [
  { name: 'BookList', label: "Books" },
  { name: 'SeriesList', label: "Series" },
]

const isAnimating = ref(false);
const current = ref<string>('BookList')
const audio = ref<boolean>(true)
const componentsMap: Record<string, any> = {
  BookList,
  SeriesList,
  // ProfilePage,
}
const currentComponent = computed(() => componentsMap[current.value])

async function fetchBooks() {
  try {
    const r1 = await api.get<Book[]>(`/author/${route.params.key}/books`)
    books.value = r1.data
    const { data: series } = await api.get<Series[]>(`/author/${route.params.key}/series`)
    seriesGroups.value = []
    for (const s of series) {
      seriesGroups.value.push({
        series: s,
        books: books.value.filter((b) => b.series_key === s.key),
      })
    }
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}


async function previewRetagAuthor() {
  try {
    showRetag.value = true
    const response = await api.get<RetagAuthor>(`/retag/author/${route.params.key}`)
    prv.value = response.data
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}

async function retagBooks(keys: string[]) {
  showRetag.value = false
  try {
    await api.post(`/retag/books`, keys)
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  fetchBooks()
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
  } catch (error: any) {
    interactiveSearch.value = true
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}

async function closeManualSearch() {
  interactiveSearch.value = false
    manualSearchVersions.value = []
    query.value = ""
    manualSearchKey.value = ""
}

async function uniteSeries(data: { series_id: string; series_ids: string[] }) {
  await api.post("/misc/union/", data)
  fetchBooks()
}

async function downloadBook(keys: string[]) {
  await runBatch(keys, key => dapi.post(`/book/${key}`, null, { params:{audio:audio.value} }), 'download', 3000)
  fetchBooks()
}

async function downloadBookManual(key: string, nzb: BookNzb) {
  try {
    await dapi.post('/guid', {book_key : key, guid : nzb.guid, download : nzb.download, name : nzb.name}, { params: { audio : audio.value } })
    interactiveSearch.value = false
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  fetchBooks()
}

async function downloadSeries(key: string) {
  try {
    await dapi.post(`/series/${key}`, null, { params: { audio : audio.value } })
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}

async function downloadAuthor() {
  try {
    downloadingAuthor.value = "throbber"
    await dapi.post(`/author/${route.params.key}`)
    downloadingAuthor.value = "download"
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
    downloadingAuthor.value = "error"
    await new Promise(resolve => setTimeout(resolve, 3000))
    downloadingAuthor.value = "download"
  }
}

async function completeAuthor() {
  try {
    completingAuthor.value = "throbber"
    await api.post(`/author/complete/${route.params.key}`)
    completingAuthor.value = "matter"
    fetchBooks()
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
    completingAuthor.value = "error"
    await new Promise(resolve => setTimeout(resolve, 3000))
    completingAuthor.value = "matter"
  }
}


async function completeSeries(key: string) {
  try {
    await api.post(`/series/complete/${key}`)
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  fetchBooks()
}

async function cleanupSeries(key: string, name: string) {
  console.log(key, name)
  try {
    await api.post(`/series/cleanup/${key}`, null, { "params": { "name" : name }})
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  fetchBooks()
}

async function confirmDeleteBook(keys: string[]) {
  showConfirmBook.value = true
  messageConfirmBook.value = `Are you sure you want to delete ${keys.length} book${keys.length > 1 ? 's' : ''}?`
  shouldDeleteBooks.value = keys
}

async function confirmEditBook(book: Book) {
  showEditor.value = true
  editedBook.value = book
}

async function confirmDeleteSeries(key: string) {
  showConfirmSeries.value = true
  messageConfirmSeries.value = `Are you sure you want to delete this Series?`
  shouldDeleteSeries.value = key
}

async function deleteBook(blocking?: boolean) {
  showConfirmBook.value = false
  await runBatch(shouldDeleteBooks.value, key => api.delete(`/book/${key}`, { params: { block: blocking } }), 'delete', 3000)
  fetchBooks()
}
async function deleteSeries() {
  showConfirmSeries.value = false
  try {
    await api.delete(`/series/${shouldDeleteSeries.value}`)
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  fetchBooks()
}

async function deleteAuthor(key: string | undefined) {
  showConfirmAuthor.value = false
  if (!key) return
  try {
    await api.delete(`/author/${key}`)
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  router.push({ name: 'Library' })
}

async function editBook(book: Book) {
  try {
    const { key, ...data } = book
    await api.patch(`/book/${key}`, data)
    showEditor.value = false
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
  fetchBooks()
}

onBeforeUnmount(async () => {
  document.documentElement.style.removeProperty('--mainColor');
})

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
.tabs {
  display: flex;
  flex-direction: row;
  gap: 4px;
  margin-top: 10px;
  margin-bottom: 5px;
}
.tabs button {
  flex: 1;
  padding: 0.5em;
  color: var(--mainColor);
  background-color: var(--offWhite);
  border: none;
  border-radius: 8px;
}
.tabs button.active {
  background: var(--mainColor);
  color: var(--backgroundWhite);
  font-weight: bold;
}
.author-page {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.author-name {
  display: flex;
  justify-content: center;
}
.author-header {
  display: flex;
  gap: 16px;
  padding: 10px 10px;
  background-color: var(--offWhite);
  border-radius: 10px;
}
.author-image {
  width: 190px;
  border-radius: 50%;
  aspect-ratio: 1/1;
  object-fit: cover;
  box-sizing: border-box;

}
.author-bio {
  border: 1px solid var(--borderColor);
  background-color: var(--backgroundWhite);
  border-radius: 8px;
  overflow: scroll;
  padding: 12px;
  box-sizing: border-box;
  margin: 0;
  margin-top: 75px;
  flex: 1;
}
div.author-image {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #ccc;
  color: #fff;
  font-weight: bold;
  font-size: 24px;
  border-radius: 50%;
  margin-bottom: 16px;
}

.download-all {
  vertical-align: middle;
  text-align: center;
  width: 190px;
}
.ctrl-btn{
  width: 35px;
  height: 50px;
  transition: transform 0.2s ease;
}
.ctrl-btn.active {
  animation: growAndTilt 0.35s ease forwards;
}

@media (max-width: 600px) {
  .author-header {
    flex-direction: column;
  }
  .author-bio{
    margin: 0;
  }
}
</style>
