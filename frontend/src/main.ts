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

const routes = [
  { path: '/',    name: 'Library', component: Library },
  { path: '/settings', name: 'Settings',  component: Settings  },
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
}

export interface InteractiveSearch{
  query: string
  nzbs: BookNzb[]
  pages: number
}

export interface Book {
  key: string
  name: string
  bild?: string
  reihe_position?: number
  b_dl_loc?: string | null
  autor_key: string
  reihe_key?: string
  a_dl_loc?: string | null
  activities?: Activity[]
}

export interface BookNzb {
  name: string
  guid: string
  size: string | number
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

const BASE = import.meta.env.VITE_API_BASE || '';
export const api    = axios.create({ baseURL: `${BASE}/api` });
export const tapi   = axios.create({ baseURL: `${BASE}/tapi` });
export const dapi = axios.create({ baseURL: `${BASE}/dapi` });


createApp(App).use(router).mount('#app')
