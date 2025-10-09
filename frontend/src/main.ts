import './style.css'
import Library from './pages/Library.vue'
import Settings  from './pages/SettingsPage.vue'
import Search from './pages/SearchPage.vue'
import Author from './pages/AuthorPage.vue'
import Test from './pages/TestPage.vue'
import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',    name: 'Library', component: Library },
  { path: '/settings', name: 'Settings',  component: Settings  },
  { path: '/author/:key', name: 'Author',  component: Author  },
  { path: '/search', name: 'Search',  component: Search  },
  { path: '/activity', name: 'Test',  component: Test  },
]

const router = createRouter({
  history: createWebHistory(), 
  routes,
})

const BASE = import.meta.env.VITE_API_BASE || '';
export const api    = axios.create({ baseURL: `${BASE}/api` });
export const tapi   = axios.create({ baseURL: `${BASE}/tapi` });
export const dapi = axios.create({ baseURL: `${BASE}/dapi` });


createApp(App).use(router).mount('#app')
