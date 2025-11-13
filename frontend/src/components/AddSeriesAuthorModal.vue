<template>
  <div v-if="visible" class="overlay">
    <div class="modal">
    <p style="overflow-wrap: anywhere;">It is possible to add a single Series as a "Fake Author". This is especially useful for multi-author series.</p>
      <input
        v-model="name"
        type="text"
        placeholder="Enter Fake Author Name..."
        class="input"
      />
      <input
        v-model="book"
        type="text"
        placeholder="Enter BookID..."
        class="input"
      />
      <div class="actions">
        <button :disabled="adding" class="ctrl-btn material-symbols-outlined" @click="submit">save</button>
        <button :disabled="adding" class="ctrl-btn material-symbols-outlined" @click="$emit('cancel')">cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  visible: boolean
  adding: boolean
}>()
const emit = defineEmits<{
  (e: 'submit', data: {name: string, entry_id: string}): void;
  (e: 'cancel'): void
}>()

const book = ref('')
const name = ref('')

function submit() {
  emit('submit', {name: name.value, entry_id: book.value})
  book.value = ''
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal {
  background: var(--offWhite);
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 420px;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
.input {
  padding: 0.4rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>
