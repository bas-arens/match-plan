import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '@/stores/authStore.js'

import HomePage      from '@/pages/HomePage.vue'
import SettingsPage  from '@/pages/SettingsPage.vue'
import MatchPlanPage from '@/pages/MatchPlanPage.vue'
import LoginPage     from '@/pages/LoginPage.vue'

const routes = [
  { path: '/',          redirect: '/calendar' },
  { path: '/login',     component: LoginPage },
  { path: '/calendar',  component: HomePage,      meta: { requiresAuth: true } },
  { path: '/settings',  component: SettingsPage,  meta: { requiresAuth: true } },
  { path: '/matchplan', component: MatchPlanPage, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard — only active once the backend supports authentication.
// Set VITE_REQUIRE_AUTH=true in .env to enable.
router.beforeEach((to) => {
  const requiresAuth = to.meta.requiresAuth && import.meta.env.VITE_REQUIRE_AUTH === 'true'
  if (requiresAuth && !authStore.token) return '/login'
})

export default router
