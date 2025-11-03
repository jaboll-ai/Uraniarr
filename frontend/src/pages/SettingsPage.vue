<template>
  <div class="settings-container">
    <h2>Settings</h2>
    <form @submit.prevent="saveSettings" class="settings-form">
      <div class="setting-item" v-for="(cfg, key) in settings" :key="key">
        <label :for="key + '-input'" class="setting-label">{{ key }}</label>
        <input v-if="cfg.input_type !== 'select'" :id="key + '-input'" v-model="cfg.value" :type="cfg.input_type" class="setting-input"/>
        <select v-else :id="key + '-input'" v-model="cfg.value" class="setting-select">
          <option v-for="opt in cfg.options" :key="opt" :value="opt">{{ opt }}</option>
        </select>
      </div>
      <button type="submit" class="save-btn">Save</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/main.ts'

interface ConfigEntry {
  value: string;
  input_type: string;
  options?: string[];
}
const settings = ref<Record<string, ConfigEntry>>({})

onMounted(async () => {
  getSettings()
})

async function getSettings() {
  try {
    const { data } = await api.get<Record<string, ConfigEntry>>('/settings')
    settings.value = data
  } catch (err) {
    console.error('Failed to load settings', err)
  }
}

async function saveSettings() {
  try {
    await api.patch('/settings', Object.fromEntries(
      Object.entries(settings.value).map(([key, cfg]) => [key, cfg.value])
    ) )
    alert('Settings saved!')
  } catch (err: any) {
    alert('Could not save settings:\n' + err.response?.data?.detail || '')
    getSettings()
  }
}
</script>

<style scoped>
.settings-container {
  padding: 16px;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.settings-form {
  display: flex;
  flex-direction: column;
}

.settings-heading {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 16px;
}

.setting-item {
  margin-bottom: 16px;
}

.setting-label {
  display: block;
  font-weight: 500;
  margin-bottom: 4px;
}

.setting-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
</style>
