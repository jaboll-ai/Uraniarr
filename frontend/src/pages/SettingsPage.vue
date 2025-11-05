<template>
  <div class="settings-container">
    <h2 class="settings-title">Settings</h2>

    <form @submit.prevent="saveSettings" class="settings-form">
      <div class="setting-item" v-for="(cfg, key) in settings" :key="key">
        <div class="setting-label-row">
          <label :for="key + '-input'" class="setting-label">
            {{ settingNames[key] || key }}
          </label>

          <span class="tooltip" v-if="tooltips[key]">
            <span class="tooltip-icon">?</span>
            <span class="tooltip-text">{{ tooltips[key] }}</span>
          </span>
        </div>

        <input
          v-if="cfg.input_type !== 'select'"
          :id="key + '-input'"
          v-model="cfg.value"
          :type="cfg.input_type"
          class="setting-input"
        />

        <select
          v-else
          :id="key + '-input'"
          v-model="cfg.value"
          class="setting-select"
        >
          <option
            v-for="opt in cfg.options"
            :key="opt"
            :value="opt"
          >
            {{ opt }}
          </option>
        </select>
      </div>

      <button type="submit" class="btn material-symbols-outlined">save</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, toRaw } from 'vue'
import { api } from '@/main.ts'

interface ConfigEntry {
  value: string
  input_type: string
  options?: string[]
}

const originalSettings = ref<Record<string, ConfigEntry>>({})
const settings = ref<Record<string, ConfigEntry>>({})

const settingNames: Record<string, string> = {
  indexer_url: 'Indexer URL',
  indexer_apikey: 'Indexer API Key',
  indexer_prowlarr: 'Use Prowlarr Integration',
  indexer_audio_category: 'Audio Category ID',
  indexer_book_category: 'Book Category ID',
  downloader_url: 'Downloader URL',
  downloader_apikey: 'Downloader API Key',
  downloader_type: 'Downloader Type',
  downloader_category: 'Downloader Category',
  audio_path: 'Audio Storage Path',
  book_path: 'Book Storage Path',
  import_poll_interval: 'Import Poll Interval (seconds)',
  rescan_interval: 'Rescan Interval (seconds)',
  reimport_interval: 'Reimport Interval (seconds)',
  indexer_timeout: 'Indexer Timeout (seconds)',
  audio_extensions_rating: 'Allowed Audio Extensions',
  book_extensions: 'Allowed Book Extensions',
  language: 'Language',
  playwright: 'Enable Playwright Scraping',
  skip_cache: 'Skip Cache',
  ignore_safe_delete: 'Ignore Safe Delete',
  known_bundles: 'Known Bundle Names'
}

const tooltips: Record<string, string> = {
  indexer_url: 'Base URL of your indexer (e.g. Prowlarr or Newznab).',
  indexer_apikey: 'API key used to authenticate with your indexer.',
  indexer_prowlarr: 'Toggle if your indexer runs via Prowlarr integration.',
  indexer_audio_category: 'Category ID for audio downloads (e.g. 3000).',
  indexer_book_category: 'Category ID for ebook downloads (e.g. 7000).',
  downloader_url: 'Base URL of your downloader (e.g. SABnzbd, NZBGet).',
  downloader_apikey: 'API key for your downloader.',
  downloader_type: 'Downloader type (e.g. sab or nzbget).',
  downloader_category: 'Category name in your downloader for this app.',
  audio_path: 'Folder path where audio files will be stored.',
  book_path: 'Folder path where book files will be stored.',
  import_poll_interval: 'Interval in seconds between import checks for downloaded files. (0 to disable imports)',
  rescan_interval: 'Interval in seconds between library rescans. Check if the books in the database still exist in filesystem. (0 to disable availability checks)',
  reimport_interval: 'Interval in seconds between reimport checks. The files in downloader or library folder are tried to be matched against books in database (0 to disable reimporting)',
  indexer_timeout: 'Timeout in seconds for indexer API calls.',
  audio_extensions_rating: 'Audio file extensions to consider (comma-separated).',
  book_extensions: 'Book file extensions to consider (comma-separated).',
  language: 'Desired Language of Uraniarr, only one supported at a time currently. (ISO 639-1 or -2 e.g. "eng")',
  playwright: 'Use playwright instead of cloudscraper. (Only toggle if necessary)',
  skip_cache: 'Force skip of local cache (useful for debugging).',
  ignore_safe_delete: 'ONLY enable if Uraniarr is importing from a custom category.',
  known_bundles: 'List of known boxset/bundle names (comma-separated).'
}

onMounted(async () => {
  getSettings()
})

async function getSettings() {
  try {
    const { data } = await api.get<Record<string, ConfigEntry>>('/settings')
    settings.value = data
    originalSettings.value = JSON.parse(JSON.stringify(data))
  } catch (err) {
    console.error('Failed to load settings', err)
  }
}

function getChangedFields() {
  const patch: Record<string, unknown> = {}
  const current = toRaw(settings.value)
  const original = toRaw(originalSettings.value)

  for (const [key, cfg] of Object.entries(current)) {
    const oldVal = (original[key] || {}).value
    const newVal = cfg.value
    if (newVal !== oldVal) {
      patch[key] = newVal
    }
  }
  return patch
}

async function saveSettings() {
  const patch = getChangedFields()
  if (Object.keys(patch).length === 0) {
    alert('Nothing changed')
    return
  }
  try {
    await api.patch('/settings', patch)
    alert('Settings saved!')
    await getSettings()
  } catch (err: any) {
    alert('Could not save settings:\n' + (err.response?.data?.detail || ''))
    await getSettings()
  }
}
</script>

<style scoped>
.settings-container {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  flex: 1;
}

.settings-title {
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  background: var(--offWhite);
  border-radius: 10px;
  padding: 1rem;
}

.setting-item:hover {
  background: color-mix(in srgb, var(--mainColor) 20%, var(--offWhite) 90%)
}

.setting-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.4rem;
  gap: 0.5rem;
}

.setting-label {
  font-weight: 500;
  font-size: 1rem;
  flex: 1;
}

.setting-input,
.setting-select {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
  transition: border 0.2s, box-shadow 0.2s;
}

.setting-input:focus,
.setting-select:focus {
  border-color:var(--mainColor);
  outline: none;
  box-shadow: 0 0 0 2px alpha(var(--mainColor), 0.2);
}

/* Tooltip */
.tooltip {
  position: relative;
  display: inline-block;
}

.tooltip-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background:var(--mainColor);
  color: #fff;
  border-radius: 50%;
  font-size: 0.8rem;
  font-weight: bold;
  cursor: default;
}

.tooltip-text {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  transform: translate(-105%, -70%);
  background: #333;
  color: #fff;
  padding: 0.5rem;
  border-radius: 6px;
  width: 220px;
  font-size: 0.85rem;
  line-height: 1.2;
  text-align: center;
  transition: opacity 0.2s ease;
  pointer-events: none;
  z-index: 10;
}

.tooltip:hover .tooltip-text {
  visibility: visible;
  opacity: 1;
}

.btn{
  margin-left: auto;
  background-color: var(--mainColor);
  color: #FFF;
  padding: 10px;
}
</style>
