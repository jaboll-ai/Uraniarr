<template>
  <BookList :showBox="false" :books="books" :seriesGroups="[]"
      :audio="false" :suppressMap="supressMap" @deleteBook="confirmUnblockBook"></BookList>

  <ConfirmModal
    :visible="showConfirmBook"
    :message="message"
    @confirm="unblockBook"
    @cancel="showConfirmBook = false"
  />
</template>

<script setup lang="ts">
import BookList from '@/components/BookList.vue';
import ConfirmModal from '@/components/ConfirmModal.vue';
import { api, type Book } from '@/main';
import { notify } from '@kyvg/vue3-notification';
import { onMounted, ref } from 'vue';

const books = ref<Book[]>([])
const supressMap = ref({
  download: true,
  search: true,
  edit: true
})
const showConfirmBook = ref(false)
const unblockedBook = ref<string[]>([])
const message = ref("")

async function confirmUnblockBook(keys: string[]) {
  showConfirmBook.value = true
  message.value = `Are you sure you want to unblock ${keys.length} book${keys.length > 1 ? 's' : ''}?\n\n(Keep in mind you still have to re-add the book to the Author)`
  unblockedBook.value = keys
}


async function unblockBook(){
  try{
    for (const key of unblockedBook.value){
      await api.delete(`/book/${key}`)
    }
    fetchBlocked()
    showConfirmBook.value = false
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}

onMounted(async () => {
  fetchBlocked()
})

async function fetchBlocked(){
  try{
   const response = await api.get<Book[]>('/books/blocked')
   books.value = response.data
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}
</script>

<style scoped>

</style>
