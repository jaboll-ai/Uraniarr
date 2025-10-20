<template>
  <div v-if="visible" class="overlay">
    <div class="modal">
      <h2>Edit: {{ form.name || 'Untitled Book' }}</h2>
      <form @submit.prevent="$emit('editBook', form)">
        <label>
          Name:
          <div>
            <input list="titles" v-model="form.name" required />
            <datalist id="titles">
              <option v-for="a in titles" :key="a" :value="a" />
            </datalist>
          </div>
        </label>

        <label>
          Author Key:
          <input v-model="form.autor_key" required />
        </label>

        <label>
          Series (Reihe) Key:
          <input v-model="form.reihe_key" />
        </label>

        <label>
          Series Position:
          <input type="number" step="0.1" v-model.number="form.reihe_position" />
        </label>

        <label>
          Bild URL:
          <input v-model="form.bild" />
        </label>

        <label>
          A DL Location:
          <input v-model="form.a_dl_loc" />
        </label>

        <label>
          B DL Location:
          <input v-model="form.b_dl_loc" />
        </label>

        <div class="actions">
          <button class="btns material-symbols-outlined" type="submit">save</button>
          <button class="btns material-symbols-outlined" type="button" @click="$emit('close')">cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch, onMounted } from 'vue'
import { api } from '@/main';
import type { Book } from '@/main.ts'


const props = defineProps<{
  visible: boolean
  book: Book
}>()

const form = reactive<Book>({ ...props.book })
const titles = ref<string[]>([])

// Reinitialize when new book prop comes in
watch(() => props.book, (newBook) => {
  Object.assign(form, newBook)
}, { immediate: true })


onMounted( async () => {
  await getTitles()
})
async function getTitles() {
  const resp = await api.get<string[]>(`/book/titles/${props.book.key}`)
  titles.value = resp.data
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal {
  background-color: var(--backgroundWhite);
  padding: 20px;
  width: 500px;
  border-radius: 8px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h2 {
  margin-top: 0;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

label {
  display: block;
  font-weight: 500;
  margin-bottom: 10px;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

.btns{
  padding: 8px;
}
</style>
