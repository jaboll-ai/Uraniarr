<template>
  <div v-if="loading" class="placeholder">
    <span class="symbol material-symbols-outlined no-select">progress_activity</span>
  </div>
  <div v-else class="search-author">
    <div class="author-header" v-for="author in authors" :key="author.key">
      <h2 class="author-name">{{ author.name }}</h2>
      <div class="author-info">
        <img v-if="author.bild" :src="author.bild" :alt="author.name" class="author-image" />
        <div v-else class="author-image">{{ getInitials(author.name) }}</div>
        <p class="author-bio">{{ author.bio }}</p>
      </div>
      <div style="display: flex;">
        <div style="flex-grow: 1;"></div>
        <button :disabled="isDisabled(author.key)" class="add-button" @click="add(author.key, author.name)">{{ authorStatus[author.key]?.adding ? dots : authorStatus[author.key]?.added ? 'Added' : 'Add' }}</button>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted, onUnmounted, watch, reactive, computed } from 'vue'
import { tapi, api } from '@/main.ts'
import { getInitials } from '@/utils.ts'
import type { Author } from '@/main.ts'

const route = useRoute()

const authors = ref<Author[]>([])
const loading = ref(false)
const authorStatus = reactive<Record<string, { adding: boolean; added: boolean }>>({})
const dots = ref('')
let timer: number

const isDisabled = computed(() => (author: string) => {
  const status = authorStatus[author]
  return status ? status.adding || status.added : false
})

async function add(author: string, name: string) {
  authorStatus[author].adding = true
  console.log("added pressed")
  try {
    await api.post(`/author/${author}`, {}, { params: { name: name } })
    authorStatus[author].added = true
  } finally {
    authorStatus[author].adding = false
  }
}

async function search() {
  try {
    loading.value = true
    const response = await tapi.get<Author[]>("/search", { params: { q: route.query.q } })
    loading.value = false
    authors.value = response.data
    for (const author of authors.value) {
      try {
        await api.get(`/author/${author.key}`)
        console.log("found em")
        authorStatus[author.key] = { adding: false, added: true }
      } catch(err) {
        console.log("not found")
        authorStatus[author.key] = { adding: false, added: false }
      }
    }
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
  console.log(authorStatus)
}

onMounted(async () => {
  search()
  timer = window.setInterval(() => {
    dots.value = dots.value.length < 3 ? dots.value + '.' : ''
  }, 500)
})

watch(
  () => route.query.q,
  (newQ, oldQ) => {
    if (newQ !== oldQ) {
      search()
    }
  }
)

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.search-author {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.author-header {
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 10px;
}
.author-info {
  display: flex;
  align-items: center;
  gap: 16px;
  max-height: 140px;
}
.author-image {
  min-width: 100px;
  border-radius: 50%;
  aspect-ratio: 1/1;
  object-fit: cover;
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
}
.author-name{
  padding-left: 10px;
  padding-right: 10px;
  padding-top: 10px;
  margin: 0;
}
.add-button {
  width: 70px;
  padding: 8px 0px;
  border-radius: 8px;
  margin: 0px 0px 0px 0px;
  border: none;
  background-color: #115300;
  color: #fff;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease
}
.add-button:disabled {
  background-color: #ccc;
  color: #666;
  opacity: 0.7;
}
.adding-loading {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-weight: bold;
  background-color: #DDD;
  padding: 8px 16px;
  border-radius: 8px;
  border-width: 2px;
  border: #115300 solid 2px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.author-bio {
  border: 1px solid var(--borderColor);
  background-color: var(--backgroundWhite);
  border-radius: 8px;
  overflow: auto;
  word-break: break-word;
  overflow-wrap: break-word;
  min-width: 0;
  padding: 12px;
  box-sizing: border-box;
  margin: 0;
  max-height: 98px;
}
.placeholder{
  display: flex;
  flex-grow: 1;
  justify-content: center;
  align-items: center;
  color: var(--fontColor);
  flex-direction: column;
  margin: 0 200px
}
.symbol{
  font-size: 100pt;
  animation: spin 2s ease-in-out infinite;
}
</style>