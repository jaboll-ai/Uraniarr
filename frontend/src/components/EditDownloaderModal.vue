<template>
  <div v-if="visible" class="overlay">
    <div class="modal">
      <h2>Edit: {{ form.name || "Unnamed Downloader" }}</h2>

      <form @submit.prevent="handleSubmit">
        <label>
          Name:
          <input v-model="form.name" required />
        </label>

        <label>
          URL:
          <input v-model="form.url" required />
        </label>

        <label>
          API Key:
          <input v-model="form.apikey" required />
        </label>

        <label>
          Type:
          <input v-model="form.type" required />
        </label>

        <label class="checkbox">
          <input type="checkbox" v-model="form.audio" />
          Use downloader for audio
        </label>

        <label class="checkbox">
          <input type="checkbox" v-model="form.book" />
          Use downloader for book
        </label>

        <label>
          Downloader Category:
          <input v-model="form.download_categories" />
        </label>

        <div class="actions">
          <button class="btns material-symbols-outlined" type="submit">save</button>
          <button class="btns material-symbols-outlined" type="button" @click="$emit('close')">close</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import type { Downloader } from "@/main.ts";

const props = defineProps<{
  visible: boolean;
  downloader: Downloader;
  idx: number;
}>();

const emit = defineEmits<{
    (e: 'save', payload: { idx: number; downloader: Downloader }): void
    (e: 'close'): void
}>();

// --- Local form state ---
const form = reactive({
  name: props.downloader.name,
  url: props.downloader.url,
  apikey: props.downloader.apikey,
  type: props.downloader.type,
  audio: props.downloader.audio,
  book: props.downloader.book,
  download_categories: props.downloader.download_categories,
});

// --- Re-init form when new indexer is passed ---
watch(
  () => props.downloader,
  (newIdx) => {
    Object.assign(form, {
      name: newIdx.name,
      url: newIdx.url,
      apikey: newIdx.apikey,
      type: newIdx.type,
      audio: newIdx.audio,
      audio_categories: [...newIdx.download_categories],
    });
  },
  { immediate: true }
);

// --- Validation ---
function isValid() {
  return (
    form.name.trim() &&
    form.url.trim() &&
    form.apikey.trim() &&
    form.type.trim()
  );
}

function handleSubmit() {
  if (!isValid()) return;

  const output: Downloader = {
    name: form.name,
    url: form.url,
    apikey: form.apikey,
    type: form.type,
    audio: form.audio,
    book: form.book,
    download_categories: form.download_categories,
  };

  emit("save", { idx: props.idx, downloader: output });
}
</script>

<style scoped>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  justify-content: center;
  align-items: center;
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

label {
  display: block;
  font-weight: 500;
  margin-bottom: 12px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
}

input[type="text"],
input[type="url"],
input[type="password"],
input:not([type="checkbox"]) {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btns {
  padding: 8px;
  cursor: pointer;
}
</style>
