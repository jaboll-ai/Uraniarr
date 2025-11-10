<template>
  <div v-if="visible" class="overlay">
    <div class="modal">
      <div style="text-align:center; font-size: 14pt;"><span style="font-weight: bold;">{{ author.name }}</span> Retag
        Preview</div>
      <div class="paths">
        <div v-for="retag in author.retags" :key="retag.book" class="section retag-item">
          <div class="retag-header">
            <div style="display: flex; align-items: center; gap: 6px;">
              <input type="checkbox" v-model="selectedBooks" :value="retag.book" />
              <span class="book-title">{{ retag.name }}</span>
            </div>
            <span class="book-id">({{ retag.book }})</span>
          </div>

          <div v-if="retag.retag.old_audio || retag.retag.new_audio" class="subsection">
            <div>Audio</div>
            <div v-if="!retag.retag.old_audio">
              <span class="noop">No file downloaded</span>
            </div>
            <div v-else-if="!retag.retag.new_audio">
              <span class="noop">Nothing to do</span>
            </div>
            <div v-else v-html="diffDisplay(retag.retag.old_audio, retag.retag.new_audio)" class="diff"></div>
          </div>

          <div v-if="retag.retag.old_book || retag.retag.new_book" class="subsection">
            <div>Book</div>
            <div v-if="!retag.retag.old_book">
              <span class="noop">No file downloaded</span>
            </div>
            <div v-else-if="!retag.retag.new_book">
              <span class="noop">Nothing to do</span>
            </div>
            <div v-else v-html="diffDisplay(retag.retag.old_book, retag.retag.new_book)" class="diff"></div>
          </div>
        </div>
      </div>

      <div class="actions">
        <div style="display: flex; align-items: center; gap: 5px; margin-right: auto;">
          <input type="checkbox" v-model="allSelected" @change="toggleSelectAll" />
          <label style="font-size: 0.9rem; user-select: none;">Select all</label>
        </div>

        <button class="btns material-symbols-outlined" @click="emit('retagBooks', selectedBooks)"
          title="Apply selected retags">
          check
        </button>
        <button class="btns material-symbols-outlined" @click="handleCancel" title="Cancel">
          cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { diffDisplay } from '@/utils.ts'
import type { RetagAuthor } from '@/main.ts'

const props = defineProps<{
  visible: boolean
  author: RetagAuthor
}>()

const emit = defineEmits<{
  (e: 'retagBooks', keys: string[]): void
  (e: 'cancel'): void
}>()

const selectedBooks = ref<string[]>([])
const allSelected = ref(true)

watch(
  () => props.author.retags,
  (retags) => {
    if (retags?.length) {
      selectedBooks.value = retags.map(r => r.book)
      allSelected.value = true
    }
  },
  { immediate: true }
)

function toggleSelectAll() {
  if (allSelected.value) {
    selectedBooks.value = props.author.retags.map(r => r.book)
  } else {
    selectedBooks.value = []
  }
}

function handleCancel() {
  emit('cancel')
}
</script>

<style scoped>
.modal {
  background: var(--offWhite);
  padding: 1.5rem 2rem;
  padding-bottom: 0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 400px;
  max-height: 80vh;
  overflow-y: auto;
}

.paths {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section {
  border: 1px solid var(--borderColor);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  background: var(--backgroundWhite);
  display: flex;
  flex-direction: column;
}

.retag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  border-bottom: 1px solid var(--borderColor);
}

.book-title {
  font-size: 1rem;
}

.book-id {
  font-size: 0.85rem;
  color: gray;
}

.subsection {
  margin-top: 5px;
}

.diff {
  font-family: monospace;
  word-break: break-all;
}

.noop {
  opacity: 0.8;
}

.same {
  color: gray;
  font-size: 12pt;
}

.actions {
  position: sticky;
  bottom: 0;
  gap: 5px;
  background: var(--offWhite);
  display: flex;
  justify-content: flex-end;
  padding-top: 10px;
  padding-bottom: 10px;
  margin-top: auto;
  border-top: 1px solid var(--borderColor);
}
</style>
