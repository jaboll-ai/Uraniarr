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


        <select
          v-if ="cfg.input_type === 'select'"
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
        <IndexerList v-else-if="key === 'indexers'" :indexers="(settings.indexers?.value as Indexer[]) || []"
        @edit-indexer="editIndexer"/>
        <DownloaderList v-else-if="key === 'downloaders'" :downloaders="(settings.downloaders?.value as Downloader[]) || []"
        @edit-downloader="editDownloader"/>
        <input
          v-else
          :id="key + '-input'"
          v-model="cfg.value"
          :type="cfg.input_type"
          class="setting-input"
        />
      </div>

      <button type="submit" class="btn material-symbols-outlined">save</button>
    </form>
  </div>
  <EditIndexerModal v-if="indexer" :indexer="indexer" :idx="indexerIdx" :visible="showModalIndexer"
  @close="showModalIndexer=false" @save="changeIndexer"/>
  <EditDownloaderModal v-if="downloader" :downloader="downloader" :idx="downloaderIdx" :visible="showModalDownloader"
  @close="showModalDownloader=false" @save="changeDownloader"/>
</template>

<script setup lang="ts">
import { ref, onMounted, toRaw } from 'vue'
import { api, type Downloader, type Indexer } from '@/main.ts'
import { notify } from '@kyvg/vue3-notification'
import IndexerList from '@/components/IndexerList.vue'
import EditIndexerModal from '@/components/EditIndexerModal.vue'
import DownloaderList from '@/components/DownloaderList.vue'
import EditDownloaderModal from '@/components/EditDownloaderModal.vue'

interface ConfigEntry {
  value: string | number | boolean | Indexer[] | Downloader[]
  input_type: string
  options?: string[]
}

const originalSettings = ref<Record<string, ConfigEntry>>({})
const settings = ref<Record<string, ConfigEntry>>({})

const settingNames: Record<string, string> = {
  book_template: 'Book Template',
  audiobook_template: 'Audiobook Template',
  indexers: 'Add Indexers',
  downloaders: 'Add Downloaders',
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
  known_bundles: 'Known Bundle Names',
  import_unfinished: 'DANGEROUS: Import Unfinished Files',
  name_ratio: 'Fuzzy Name Ratio',
  ingest_path: 'Ingest Folder',
}

const tooltips: Record<string, string> = {
  book_template: 'Replaces placeholders like {{attr}} with values from the selected object. Supports simple formatting inside braces like {{book.position} - }',
  audiobook_template: 'Replaces placeholders like {{attr}} with values from the selected object. Supports simple formatting inside braces like {{book.position} - }',
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
  known_bundles: 'List of known boxset/bundle names (comma-separated).',
  import_unfinished: 'Import all files from downloader folder, even if they are not finished yet. (DANGEROUS)',
  name_ratio: 'Fuzzy ratio to match the release and the bookname (set to 0 to disable)',
  ingest_path: 'Folder to ingest books and audiobooks from. (leave blank to not ingest anything) [UNTESTED]',
}

const showModalIndexer = ref(false)
const showModalDownloader = ref(false)
const indexer = ref<Indexer>()
const indexerIdx = ref(-1)
const downloader = ref<Downloader>()
const downloaderIdx = ref(-1)


onMounted(async () => {
  getSettings()
})

async function editIndexer(idx: number) {
  indexer.value = (settings.value.indexers?.value as Indexer[])[idx] || {
    name: '',
    type: 'prowlarr',
    url: '',
    apikey: '',
    book: false,
    audio: false,
    audio_categories: [],
    book_categories: []
  }
  indexerIdx.value = idx
  showModalIndexer.value = true
}

async function editDownloader(idx: number) {
  downloader.value = (settings.value.downloaders?.value as Downloader[])[idx] || {
    name: '',
    type: 'sab',
    url: '',
    apikey: '',
    audio: false,
    download_categories: [],
  }
  downloaderIdx.value = idx
  showModalDownloader.value = true
}

async function changeIndexer({idx, indexer}: { idx: number; indexer: Indexer }) {
  if (!settings.value.indexers) return
  const editedIndexers = (settings.value.indexers.value as Indexer[]) || []
  if (idx < 0) idx = editedIndexers.length
  editedIndexers[idx] = indexer
  showModalIndexer.value = false
  settings.value.indexers.value = editedIndexers
  await saveSettings()
}

async function changeDownloader({idx, downloader}: { idx: number; downloader: Downloader }) {
  if (!settings.value.downloaders) return
  const editedDownloaders = (settings.value.downloaders.value as Downloader[]) || []
  if (idx < 0) idx = editedDownloaders.length
  editedDownloaders[idx] = downloader
  showModalDownloader.value = false
  settings.value.downloaders.value = editedDownloaders
  await saveSettings()
}

async function getSettings() {
  try {
    const { data } = await api.get<Record<string, ConfigEntry>>('/settings')
    settings.value = data
    originalSettings.value = JSON.parse(JSON.stringify(data))
  } catch (error: any) {
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
  }
}

const INDEXER_KEYS = ["name","url","apikey","type","book","audio","audio_categories","book_categories"] as const satisfies readonly (keyof Indexer)[]
const DOWNLOADER_KEYS = ["name","url","apikey","type","audio","book","download_categories"] as const satisfies readonly (keyof Downloader)[]

function changedObjects<T extends object>(newArr: T[], oldArr: T[], keys: readonly (keyof T)[]): T[] {
  const changed: T[] = []
  for (let i = 0; i < newArr.length; i++) {
    const n = newArr[i]
    const o = oldArr[i]
    if (!o) { changed.push(n); continue }
    for (const k of keys) {
      if (n[k] !== o[k]) { changed.push(n); break }
    }
  }
  return changed
}


function getChangedFields() {
  const patch: Record<string, unknown> = {}
  const current = toRaw(settings.value)
  const original = toRaw(originalSettings.value)

  for (const [key, cfg] of Object.entries(current)) {
    const oldVal = (original[key] || {}).value
    const newVal = cfg.value
    if (key === "indexers") {
      const changedIdxs = changedObjects(newVal as Indexer[], oldVal as Indexer[], INDEXER_KEYS)
      if (changedIdxs.length) patch[key] = changedIdxs
    }
    else if (key === "downloaders") {
      const changedDls = changedObjects(newVal as Downloader[], oldVal as Downloader[], DOWNLOADER_KEYS)
      if (changedDls.length) patch[key] = changedDls
    }
    else if (newVal !== oldVal) {
      patch[key] = newVal
    }
  }
  return patch
}

async function saveSettings() {
  const patch = getChangedFields()
  if (Object.keys(patch).length === 0) {
    notify({
      title: 'No changes detected',
      text: 'Nothing to do.',
      type: 'warn'
    })
    return
  }
  try {
    await api.patch('/settings', patch)
    notify({
      title: 'Success',
      text: 'Settings saved.',
      type: 'success'
    })
    await getSettings()
  } catch (error: any) {
    console.log(error)
    notify({
      title: 'Error',
      text: error.response.data.detail,
      type: 'error'
    })
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
