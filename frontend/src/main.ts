import './style.css'
import Library from './pages/Library.vue'
import Settings  from './pages/SettingsPage.vue'
import Search from './pages/SearchPage.vue'
import Author from './pages/AuthorPage.vue'
import Book from './pages/BookPage.vue'
import Activity from './pages/ActivityPage.vue'
import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'
import { createRouter, createWebHistory } from 'vue-router'
import Blocklist from './pages/BlocklistPage.vue'

const routes = [
  { path: '/',    name: 'Library', component: Library },
  { path: '/settings', name: 'Settings',  component: Settings  },
  { path: '/blocklist', name: 'Blocklist',  component: Blocklist  },
  { path: '/author/:key', name: 'Author',  component: Author  },
  { path: '/book/:key', name: 'Book',  component: Book  },
  { path: '/search', name: 'Search',  component: Search  },
  { path: '/activity', name: 'Activity',  component: Activity  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export interface Activity {
  created: number
  book_key: string
  nzo_id: string
  release_title: string
  status: string
  audio: boolean
}

export interface InteractiveSearch{
  query: string
  nzbs: BookNzb[]
  pages: number
}

export interface PreviewRetag{
  book: string
  name: string
  retag: {
    old_audio: string
    old_book: string
    new_audio: string | null
    new_book: string | null
  }
}

export interface RetagAuthor {
  name: string
  key: string
  retags: PreviewRetag[]
}

export interface Book {
  key: string
  name: string
  bild?: string
  position?: number
  b_dl_loc?: string | null
  autor_key: string
  series_key?: string
  a_dl_loc?: string | null
  activities: Activity[]
}

export interface BookNzb {
  name: string
  guid: string
  size: string | number
  download: string
  i_idx: number
}

export interface Author {
  name: string
  key: string
  bild: string
  bio: string
}

export interface Series {
  autor_key: string
  key: string
  name: string
}
export interface Indexer {
  name: string;
  url: string;
  apikey: string;
  type: string;
  book: boolean;
  audio: boolean;
  audio_categories: string;
  book_categories: string;
}

export interface Downloader {
  name: string;
  url: string;
  apikey: string;
  type: string;
  audio: boolean;
  book: boolean;
  download_categories: string;
}

const BASE = import.meta.env.VITE_API_BASE || '';
export const api    = axios.create({ baseURL: `${BASE}/api` });
export const tapi   = axios.create({ baseURL: `${BASE}/tapi` });
export const dapi = axios.create({ baseURL: `${BASE}/dapi` });


createApp(App).use(router).mount('#app')
