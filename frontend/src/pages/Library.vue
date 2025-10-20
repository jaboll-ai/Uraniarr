<template>
  <div class="authors">
    <AuthorCard
      v-for="author in authors"
      :key="author.key"
      :author="author"
    />
  </div>
  <button title="Add Author from Series" class="add-btn material-symbols-outlined" @click="showAdder = true">add</button>
  <AddSeriesAuthorModal :adding="adding" :visible="showAdder" @submit="addSeriesAuthor" @cancel="showAdder = false"/>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/main.ts'
import AuthorCard from '@/components/AuthorCard.vue'
import AddSeriesAuthorModal from '@/components/AddSeriesAuthorModal.vue'
import type { Author } from '@/main.ts'


const authors = ref<Author[]>([])
const showAdder = ref(false)
const adding = ref(false)
onMounted(async () => {
  getAuthors()
})


async function getAuthors(){
  const response = await api.get<Author[]>('/authors')
  authors.value = response.data
}

async function addSeriesAuthor(data: {name: string, entry_id: string}){
  adding.value = true
  await api.post("fakeauthor", data)
  adding.value = false
  showAdder.value = false
  getAuthors()
}
</script>

<style scoped>
.authors {
  flex-grow: 1;
  display: grid;
  grid-template-columns: repeat(auto-fit, 250px);
  grid-auto-rows: 250px;
  gap: 16px;.adding-loading {
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
  padding: 16px;
}

.add-btn{
  position: fixed;
  bottom: 32px;
  right: 32px;
  background: var(--mainColor);
  color: var(--backgroundWhite);
  border: none;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  font-size: 33px;
}
</style>