<template>
  <button :disabled="loading || text == 'error'" class="material-symbols-outlined" :title="title"
    @click="emit('click')">
    <VueSpinner v-if="loading" />
    <span v-else>{{ text }}</span>
  </button>
</template>

<script setup lang="ts">
import { VueSpinner } from 'vue3-spinners'

defineProps<{
  loading?: boolean
  text: string
  title?: string
}>()

const emit = defineEmits<{
  (e: 'click'): void
}>()
</script>