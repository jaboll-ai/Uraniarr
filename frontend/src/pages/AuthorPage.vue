<template>
  <div class="author-page">
    <div class="author-header">
      <div class="author-info">
        <h2 class="author-name">{{ author?.name }}</h2>
        <img v-if="author?.bild" :src="author.bild" :alt="author.name" class="author-image" />
      <div v-else-if="author" class="author-image">{{ getInitials(author.name) }}</div>
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
        <component :is="currentComponent"  @downloadBook="downloadBook"/>
      </keep-alive>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted, computed } from 'vue'
import { api, nzbapi as sabnzbdapi } from '@/main.ts'
import BookList from '@/components/BookList.vue'
import SeriesList from '@/components/SeriesList.vue'
import { getInitials } from '@/utils.ts'

const route = useRoute()

interface Author {
  name: string
  key: string
  bild: string
  bio: string
}
const author = ref<Author | null>(null)

onMounted(async () => {
  try {
    const responseA = await api.get<Author>(`/author/${route.params.key}`)
    author.value = responseA.data
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
})

const tabs = [
  { name: 'BookList',     label: 'Books'    },
  { name: 'SeriesList',  label: 'Series'  },
  { name: 'SettingsPage', label: 'Settings' },
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
    sabnzbdapi.post(`/book/${key}`)
  } catch (err) {
    console.error('Failed to send or grab nzb', err)
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
}
.author-name {
  display: flex;
  justify-content: center;
}
.author-header {
  max-height: 300px;
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
</style>
