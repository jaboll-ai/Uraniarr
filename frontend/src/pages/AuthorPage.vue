<template>
  <div class="author-page">
    <div class="author-header">
      <div class="author-info">
        <h2 class="author-name">{{ author?.name }}</h2>
        <img v-if="author?.bild" :src="author.bild" :alt="author.name" class="author-image" />
        <div v-else-if="author" class="author-image">{{ getInitials(author.name) }}</div>
        <div class="download-all">
          <button class="ctrl-btn material-symbols-outlined" @click="downloadAuthor(author?.key)">
            <VueSpinner v-if="downloadingAuthor=='throbber'"/>
            <span v-else>{{ downloadingAuthor }}</span>
          </button>
          <button class="ctrl-btn material-symbols-outlined" @click="showConfirmAuthor = true">delete</button>
          <button class="ctrl-btn material-symbols-outlined" @click="audio = !audio">{{ audio ? "headphones" : "book" }}</button>
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
          @downloadSeries="downloadSeries" @deleteSeries="confirmDeleteSeries" @deleteBook="confirmDeleteBook" @editBook="editBook"
          @cleanupSeries="cleanupSeries" @uniteSeries="uniteSeries" @searchBook="searchBook"
          :showBox="showBox" :books="books" :seriesGroups="seriesGroups" :audio="audio"/>
      </keep-alive>
    </div>
    <ConfirmModal
      :visible="showConfirmAuthor"
      message="Are you sure yopu want to delete this author?"
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
    <ManualSearch :query="query" :visible="interactiveSearch" :book="manualSearchKey" 
    :pages="manualSearchPages" :versions="manualSearchVersions"
     @close="closeManualSearch" @select="downloadBookManual" @paginate="searchBookPaginate"/>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { VueSpinner } from 'vue3-spinners'
import { ref, onMounted, computed } from 'vue'
import { api, dapi as dapi } from '@/main.ts'
import BookList from '@/components/BookList.vue'
import SeriesList from '@/components/SeriesList.vue'
import { getInitials } from '@/utils.ts'
import ConfirmModal from '@/components/ConfirmModal.vue'
import ManualSearch from '@/components/ManualSearch.vue'
import type { Author, BookNzb, Book, Series, InteractiveSearch } from '@/main.ts'

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
const messageConfirmSeries = ref("")
const shouldDeleteSeries = ref("")
const seriesGroups = ref<Array<{ series: Series; books: Book[] }>>([])
const manualSearchVersions = ref<BookNzb[]>([])
const query = ref("")
const manualSearchKey = ref("")
const manualSearchPages = ref(0)
const downloadingAuthor = ref("download")

onMounted(async () => {
  try {
    const response = await api.get<Author>(`/author/${route.params.key}`)
    author.value = response.data
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
  fetchBooks()
})
const tabs = [
  { name: 'BookList', label: "Books" },
  { name: 'SeriesList', label: "Series" },
]

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
    var b: Book[] = []
    const { data: seriesList } = await api.get<Series[]>(`/author/${route.params.key}/series`)
    const groups = await Promise.all(
      seriesList.map(async (s: Series) => {
        const { data: books } = await api.get<Book[]>(`/series/${s.key}/books`)
        books.sort((a: Book, b: Book) => (a.reihe_position ?? 0) - (b.reihe_position ?? 0))
        b = b.concat(books)
        return { series: s, books }
      })
    )
    books.value = b
    seriesGroups.value = groups
  } catch (err) {
    console.error('Failed to load series or books', err)
  }
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

async function uniteSeries(data: { series_id: string; series_ids: string[] }) {
  await api.post("/misc/union/", data)
  fetchBooks()
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
    await dapi.post('/guid', {book_key : key, guid : nzb.guid, name : nzb.name}, { params: { audio : audio.value } })
  } catch (err) {
    console.error('Failed to download book', err)
  }
}

async function downloadSeries(key: string) {
  try {
    await dapi.post(`/series/${key}`, null, { params: { audio : audio.value } })
  } catch (err) {
    console.error('Failed to download Series', err)
  }
}

async function downloadAuthor(key:string | undefined) {
  if (!key) return
  try {
    downloadingAuthor.value = "throbber"
    await dapi.post(`/author/${key}`)
    downloadingAuthor.value = "download"
  } catch (err) {
    console.error('Failed to download Author', err)
    downloadingAuthor.value = "error"
    await new Promise(resolve => setTimeout(resolve, 3000))
    downloadingAuthor.value = "download"
  }
}

async function completeSeries(key: string) {
  try {
    await api.post(`/series/complete/${key}`)
  } catch (err) {
    console.error('Failed to complete series', err)
  }
  fetchBooks()
}

async function cleanupSeries(key: string, name: string) {
  console.log(key, name)
  try {
    await api.post(`/series/cleanup/${key}`, null, { "params": { "name" : name }})
  } catch (err) {
    console.error('Failed to cleanup series', err)
  }
  fetchBooks()
}

async function confirmDeleteBook(keys: string[]) {
  showConfirmBook.value = true
  messageConfirmBook.value = `Are you sure you want to delete ${keys.length} book${keys.length > 1 ? 's' : ''}?`
  shouldDeleteBooks.value = keys
}

async function confirmDeleteSeries(key: string) {
  showConfirmSeries.value = true
  messageConfirmSeries.value = `Are you sure you want to delete this Series?`
  shouldDeleteSeries.value = key
}

async function deleteBook(blocking?: boolean) {
  console.log(blocking)
  showConfirmBook.value = false
  try {
    for (const key of shouldDeleteBooks.value) {
      await api.delete(`/book/${key}`, { params: { block: blocking } })
    }
  } catch (err) {
    console.error('Failed to delete book', err)
  }
  fetchBooks()
}

async function deleteSeries() {
  showConfirmSeries.value = false
  try {
    await api.delete(`/series/${shouldDeleteSeries.value}`)
  } catch (err) {
    console.error('Failed to delete series', err)
  }
  fetchBooks()
}

async function deleteAuthor(key: string | undefined) {
  showConfirmAuthor.value = false
  if (!key) return
  try {
    await api.delete(`/author/${key}`)
  } catch (err) {
    console.error('Failed to delete Author', err)
  }
  router.push({ name: 'Library' })
}

async function editBook(book: Book) {
  try {
    await api.patch(`/book/${book.key}`, book)
  } catch (err) {
    console.error('Failed to edit book', err)
  }
  fetchBooks()
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
  width: 50px;
  height: 50px;
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
