<template>
  <div v-if="loading" class="loading-screen">
    Loading…
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
        <button class="add-button" @click="add(author.key)">Add</button>
      </div>
      <div v-if="adding[author.key]" class="adding-loading">
        <span>Adding</span>
        <span>.{{ dots }}</span>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { tapi, api } from '@/main.ts'
import { getInitials } from '@/utils.ts'

const route = useRoute()

interface Author {
  name: string
  key: string
  bild: string
  bio: string
}

const authors = ref<Author[]>([])
const loading = ref(false)
interface BoolMap { [key: string]: boolean }
const adding = ref<BoolMap>({})
const dots = ref('')
let timer: number

async function add(author: string){
  adding.value[author] = true
  try {
    await api.post(`/author/${author}`)
  } finally {
    adding.value[author] = false
  }
}

async function search() {
    try {
    loading.value = true
    const response = await tapi.get<Author[]>("/search", { params: { q: route.query.q } })
    loading.value = false
    authors.value = response.data
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
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
  width: min-content;
  padding: 8px 16px;
  border-radius: 8px;
  margin: 0px 0px 0px 0px;
  border: none;
  background-color: #115300;
  color: #fff;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease
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
</style>