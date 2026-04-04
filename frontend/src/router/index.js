import { createRouter, createWebHistory } from 'vue-router'

import HomePage from '@/pages/HomePage.vue'
import SettingsPage from '@/pages/SettingsPage.vue'
import MatchPlanPage from '@/pages/MatchPlanPage.vue'

const routes = [
  { path: '/', redirect: '/calendar' },
  { path: '/calendar', component: HomePage },
  { path: '/settings', component: SettingsPage },
  { path: '/matchplan', component: MatchPlanPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
