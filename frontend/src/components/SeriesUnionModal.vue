<template>
  <div v-if="visible" class="modal-overlay">
    <div class="modal">
      <h3>Select Items</h3>

      <div v-if="loading">Loading...</div>

      <div v-else>
        <div v-for="item in items" :key="item.key">
          <label>
            <input
              type="checkbox"
              :value="item.key"
              v-model="selected"
            />
            {{ item.name }}
          </label>
        </div>
      </div>

      <div class="modal-actions">
        <button class="ctrl-btn material-symbols-outlined" @click="$emit('unite', selected)">save</button>
        <button class="ctrl-btn material-symbols-outlined" @click="$emit('close')">cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Series {
  autor_key: string
  name: string
  key: string
}

defineProps<{
  items: Series[]
  seriesID: string
  visible: boolean
}>()

defineEmits<{
  (e: 'unite', selected: string[]): void
  (e: 'close'): void
}>()

const selected = ref<string[]>([])
const loading = ref(false)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
}

.modal-actions {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.ctrl-btn {
  color: var(--darkGray);
  padding: 0px 8px;
  color: #fff;
  margin: 10px 2px;
}
</style>
