import './style.css'
import Library from './pages/Library.vue'
import Settings  from './pages/SettingsPage.vue'
import Search from './pages/SearchPage.vue'
import Author from './pages/AuthorPage.vue'
import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',    name: 'Library', component: Library },
  { path: '/settings', name: 'Settings',  component: Settings  },
  { path: '/author/:key', name: 'Author',  component: Author  },
  { path: '/search', name: 'Search',  component: Search  },
]

const router = createRouter({
  history: createWebHistory(), 
  routes,
})

export const api = axios.create({ baseURL: 'http://localhost:8000/api' })
export const tapi = axios.create({ baseURL: 'http://localhost:8000/tapi' })
export const mapi = axios.create({ baseURL: 'http://localhost:8000/mapi' })
export const nzbapi = axios.create({ baseURL: 'http://localhost:8000/nzbapi' })


createApp(App).use(router).mount('#app')
