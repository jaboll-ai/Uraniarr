<template>
  <router-link :to="{ name: 'Author', params: { key: author.key} }" class="author-card-link">
    <div class="author-card">
      <img v-if="author.bild" :src="author.bild" :alt="author.name" class="author-image" />
      <div v-else class="author-image">{{ getInitials(author.name) }}</div>
      <h2 class="author-name">{{ author.name }}</h2>
    </div> 
  </router-link>
</template>

<script setup lang="ts">
import { getInitials } from '../utils.ts'

interface Author {
  name: string
  key: string
  bild: string
  bio: string
}

const { author } = defineProps<{
  author: Author
}>()
</script>

<style scoped>

.author-card-link {
  display: block; 
  width: 100%;
  height: 100%;
  text-decoration: none;
  color: inherit;
  display: block;
}

.author-card {
  width: 100%;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  text-align: center;
  padding: 16px;
  box-sizing: border-box;
}

.author-image {
  object-fit: cover;
  border-radius: 50%;
  height: 70%;
  width: 70%;
  margin: 0 auto 12px;
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

.author-name {
  margin: 8px 0;
  font-size: 1.25rem;
}

.author-bio {
  font-size: 0.9rem;
  color: #555;
  text-align: left;
  max-height: 6em;
  overflow: hidden;
}
</style>
