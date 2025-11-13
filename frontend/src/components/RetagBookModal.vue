<template>
    <div v-if="visible" class="overlay">
        <div class="modal">
            <div style="text-align:center; font-size: 14pt;"><span style="font-weight: bold;">{{ prv.name }}</span> Retag Preview</div>

            <div class="paths">
                <div class="section" v-if="prv.retag.old_audio || prv.retag.new_audio">
                    <div>Audio</div>
                    <div v-if="!prv.retag.old_audio">
                        <span class="noop">No file downloaded</span>
                    </div>
                    <div v-else-if="!prv.retag.new_audio">
                        <span class="noop">Nothing to do</span>
                    </div>
                    <div v-else v-html="diffDisplay(prv.retag.old_audio, prv.retag.new_audio)" class="diff"></div>
                </div>

                <div class="section" v-if="prv.retag.old_book || prv.retag.new_book">
                    <div>Book</div>
                    <div v-if="!prv.retag.old_book">
                        <span class="noop">No file downloaded</span>
                    </div>
                    <div v-else-if="!prv.retag.new_book">
                        <span class="noop">Nothing to do</span>
                    </div>
                    <div v-else v-html="diffDisplay(prv.retag.old_book, prv.retag.new_book)" class="diff"></div>
                </div>
            </div>

            <div class="actions">
                <button class="btns material-symbols-outlined" @click="emit('retagBook', [prv.book])" title="Apply retag">check</button>
                <button class="btns material-symbols-outlined" @click="handleCancel" title="Cancel">cancel</button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { diffDisplay } from '@/utils.ts'
import type { PreviewRetag } from '@/main.ts'

defineProps<{
    visible: boolean
    prv: PreviewRetag
}>()

const emit = defineEmits<{
    (e: 'retagBook', key: string[]): void
    (e: 'cancel'): void
}>()

function handleCancel() {
    emit('cancel')
}
</script>

<style scoped>
.modal {
  background: var(--offWhite);
  padding: 1.5rem 2rem;
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
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
}

.btns {
    padding: 8px;
    cursor: pointer;
}
</style>

<style>
.addedDiff {
    background-color: rgba(0, 200, 0, 0.15);
    border-radius: 3px;
    padding: 0 2px;
}

.removedDiff {
    background-color: rgba(200, 0, 0, 0.15);
    border-radius: 3px;
    padding: 0 2px;
    text-decoration: line-through;
}
</style>
