<template>
  <div v-if="visible" class="overlay">
    <div class="modal">
      <span class="message">{{ message }}</span>
      <div style="display: flex;" v-if="blocking">
        <span>Also block from future completions or searches?</span>
        <input class="selector" type="checkbox" :checked="checked" @click="checked = !checked"/>
      </div>
      <div class="actions">
        <button class="btns material-symbols-outlined" @click="$emit('confirm', checked); checked = false">check</button>
        <button class="btns material-symbols-outlined" @click="$emit('cancel'); checked = false">cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
defineProps<{ visible: boolean; message?: string, blocking?: boolean }>()
defineEmits<{
  (e: 'confirm', blocking?: boolean ): void
  (e: 'cancel'): void
}>()
const checked = ref(false)
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal {
  background: var(--backgroundWhite);
  padding: 1rem 1.5rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 240px;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
.btns{
  padding: 8px;
}

.message {
  text-align: center;
  font-weight: 500;
  font-size: large;
}

.selector {
  margin-left: 0 8px;
}
</style>
