<template>
  <div class="indexer-list">
    <div class="cards">
      <div v-for="(indexer, idx) in indexers" :key="indexer.name" class="card indexer-card">
        <div>
          <div class="title">{{ indexer.name }}</div>
          <div class="subtitle">{{ indexer.type }}</div>
        </div>
        <button type="button" class="edit-btn material-symbols-outlined" @click="$emit('editIndexer', idx)">
          edit
        </button>
      </div>

      <div type="button" class="card add-card" @click="$emit('editIndexer', indexers.length)">
        <span class="plus material-symbols-outlined">add</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Indexer } from "@/main.ts";

defineProps<{
  indexers: Indexer[];
}>();

defineEmits<{
  (e: 'editIndexer', idx: number): void
}>();
</script>

<style scoped>
.indexer-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.cards {
  display: flex;
  gap: 1.25rem;
  margin-top: 1rem;
}

.card {
  background: var(--backgroundWhite);
  border-radius: 6px;
  max-width: 260px;
  min-width: 50px;
  height: 50px;
  padding: 10px;
  display: flex;
  gap: 10px;
}

.indexer-card .title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: auto 0;
}

.indexer-card .subtitle {
  opacity: 0.7;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}



/* Add card */
.add-card {
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  width: 50px;
  height: 50px;
}

.add-card:hover .plus {
  color: white;
}

.plus {
  font-size: 36px;
  color: #bbb;
}
</style>
