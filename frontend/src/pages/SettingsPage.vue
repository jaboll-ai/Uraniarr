<template>
  <div class="settings-container">
    <h2>Settings</h2>
    <form @submit.prevent="saveSettings" class="settings-form">
      <div class="setting-item" v-for="(_, key) in settings" :key="key">
        <label :for="key + '-input'" class="setting-label">{{ key }}</label>
        <input :id="key + '-input'" v-model="settings[key]" type="text" class="setting-input"/>
      </div>
      <button type="submit" class="save-btn">Save</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/main.ts'

const settings = ref<Record<string, string>>({})

onMounted(async () => {
  try {
    const { data } = await api.get<Record<string, string>>('/settings')
    settings.value = data
  } catch (err) {
    console.error('Failed to load settings', err)
  }
})

async function saveSettings() {
  try {
    // send the full list back — your server can diff or overwrite
    await api.post('/settings', { settings: settings.value })
    alert('Settings saved!')
  } catch (err) {
    console.error('Failed to save settings', err)
    alert('Could not save settings')
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
