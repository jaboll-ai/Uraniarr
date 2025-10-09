<template>
  <div class="author-page">
    <div class="author-header">
      <div class="author-info">
        <h2 class="author-name">{{ author?.name }}</h2>
        <img v-if="author?.bild" :src="author.bild" :alt="author.name" class="author-image" />
        <div v-else-if="author" class="author-image">{{ getInitials(author.name) }}</div>
        <div class="download-all">
          <button class="ctrl-btn material-symbols-outlined" @click="downloadAuthor(author?.key)">download</button>
        </div>
      </div>
      <p class="author-bio">{{ author?.bio }}</p>
    </div>
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        @click="current = tab.name"
        :class="{ active: current === tab.name }"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="panel">
      <keep-alive>
        <component :is="currentComponent"
          @downloadBook="downloadBook" @completeSeries="completeSeries"
          @downloadSeries="downloadSeries" @deleteSeries="deleteSeries" @deleteBook="deleteBook" @editBook="editBook"
          @cleanupSeries="cleanupSeries" :showBox="showBox" :books="books"/>
      </keep-alive>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted, computed } from 'vue'
import { api, dapi as dapi } from '@/main.ts'
import BookList from '@/components/BookList.vue'
import SeriesList from '@/components/SeriesList.vue'
import { getInitials } from '@/utils.ts'

const route = useRoute()

interface Book {
  key: string
  name: string
  autor_key: string
  bild?: string
  reihe_key?: string
  reihe_position?: number
  a_dl_loc?: string
  b_dl_loc?: string
}

interface Author {
  name: string
  key: string
  bild: string
  bio: string
}
const author = ref<Author | null>(null)
const books = ref<Book[]>([])
const showBox = ref(false)

onMounted(async () => {
  try {
    const responseA = await api.get<Author>(`/author/${route.params.key}`)
    author.value = responseA.data
    const responseB = await api.get<Book[]>(`/author/${route.params.key}/books`)
    books.value = responseB.data
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
})
const tabs = [
  { name: 'BookList',     label: 'Books'    },
  { name: 'SeriesList',  label: 'Series'  },
  // { name: 'SettingsPage', label: 'Settings' },
]

const current = ref<string>('BookList')
const componentsMap: Record<string, any> = {
  BookList,
  SeriesList,
  // ProfilePage,
}
const currentComponent = computed(() => componentsMap[current.value])


async function downloadBook(key: string) {
  try {
    dapi.post(`/book/${key}`)
  } catch (err) {
    console.error('Failed to download Book', err)
  }
}

async function downloadSeries(key: string) {
  try {
    dapi.post(`/series/${key}`)
  } catch (err) {
    console.error('Failed to download Series', err)
  }
}

async function downloadAuthor(key:string | undefined) {
  if (!key) return
  try {
    dapi.post(`/author/${key}`)
  } catch (err) {
    console.error('Failed to download Author', err)
  }
}

async function completeSeries(key: string) {
  try {
    api.post(`/series/complete/${key}`)
  } catch (err) {
    console.error('Failed to complete series', err)
  }
}

async function cleanupSeries(key: string, name: string) {
  console.log(key, name)
  try {
    api.post(`/series/cleanup/${key}`, null, { "params": { "name" : name }})
  } catch (err) {
    console.error('Failed to cleanup series', err)
  }
}

async function deleteBook(keys: string) {
  const confirmDelete = confirm(`Are you sure you want to delete ${keys.length} book${keys.length > 1 ? 's' : ''}?`)
  if (!confirmDelete) return
  try {
    for (const key of keys) {
      api.delete(`/book/${key}`)
    }
  } catch (err) {
    console.error('Failed to delete book', err)
  }
}

async function deleteSeries(key: string) {
  const confirmDelete = confirm('Are you sure you want to delete this series?')
  if (!confirmDelete) return
  try {
    api.delete(`/series/${key}`)
  } catch (err) {
    console.error('Failed to delete series', err)
  }
}

async function editBook(book: Book) {
  try {
    await api.patch(`/book/${book.key}`, book)
  } catch (err) {
    console.error('Failed to edit book', err)
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
}
.ctrl-btn{
  color: var(--lightGray);
  padding: 0px 8px;
  color: #fff;
  margin: 10px 2px;
}
</style>
