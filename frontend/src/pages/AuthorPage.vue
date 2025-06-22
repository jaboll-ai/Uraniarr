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
    <div class="book-list">
      <div class="book-item" v-for="book in books" :key="book.key">
        <img :src="book.bild" :alt="book.name" class="book-icon" />
        <div class="book-info">
          <span class="book-title">{{ book.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { api } from '../main.ts'
import { getInitials } from './utils.ts'

const route = useRoute()

interface Author {
  name: string
  key: string
  bild: string
  bio: string
}
interface Book {
  name: string
  key: string
  autor_key: string
  reihe_key: string | null
  bild: string
  reihe_position: number | null
}

const books = ref<Book[]>([])
const author = ref<Author | null>(null)

onMounted(async () => {
  try {
    const responseA = await api.get<Author>(`/author/${route.params.key}`)
    const responseB = await api.get<Book[]>(`/author/${route.params.key}/books`)
    author.value = responseA.data
    books.value = responseB.data
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
})
</script>

<style scoped>
.book-list {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  gap: 12px;
  padding: 16px;
  box-sizing: border-box;
}

.book-item {
  display: flex;
  /* justify-content: space-between; */
  gap: 10%;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  background-color: #f9f9f9;
}

.book-title {
  font-size: 1rem;
  font-weight: 500;
}

.book-icon {
  width: 50px;
  height: 50px;
  aspect-ratio: 1/1;
  object-fit: cover;
  border-radius: 4px;
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
  background-color: #EEE;
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
  border: 1px solid #ddd;
  background-color: #f9f9f9;
  border-radius: 8px;
  overflow: scroll;
  padding: 12px;
  box-sizing: border-box;
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