<template>
  <div v-if="visible" class="overlay">
    <div class="modal">
      <p>{{ message }}</p>
      <div class="actions">
        <button class="btns material-symbols-outlined" @click="$emit('confirm')">check</button>
        <button class="btns material-symbols-outlined" @click="$emit('cancel')">cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean; message?: string }>()
const emit = defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>()
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
  background: white;
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

</style>
