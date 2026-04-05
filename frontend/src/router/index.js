// ─────────────────────────────────────────────────────────────────────────────
// File:    src/router/index.js
// Author:  MatchPlan
// Purpose: Vue Router configuration — defines all application routes and
//          the navigation guard that enforces authentication.
//
// Routes:
//   /            → redirects to /calendar
//   /login       → LoginPage       (public)
//   /calendar    → HomePage        (protected)
//   /settings    → SettingsPage    (protected)
//   /matchplan   → MatchPlanPage   (protected)
//   /:pathMatch  → NotFoundPage    (catch-all 404)
//
// Auth guard:
//   Enabled only when VITE_REQUIRE_AUTH=true is set in .env.
//   Redirects unauthenticated users to /login.
// ─────────────────────────────────────────────────────────────────────────────

import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '@/stores/authStore.js'

import HomePage      from '@/pages/HomePage.vue'
import SettingsPage  from '@/pages/SettingsPage.vue'
import MatchPlanPage from '@/pages/MatchPlanPage.vue'
import LoginPage     from '@/pages/LoginPage.vue'
import NotFoundPage  from '@/pages/NotFoundPage.vue'

const routes = [
  { path: '/',          redirect: '/calendar' },
  { path: '/login',     component: LoginPage },
  { path: '/calendar',  component: HomePage,      meta: { requiresAuth: true } },
  { path: '/settings',  component: SettingsPage,  meta: { requiresAuth: true } },
  { path: '/matchplan', component: MatchPlanPage, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', component: NotFoundPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard — activate by setting VITE_REQUIRE_AUTH=true in .env.
// Once the backend supports authentication, flip this flag and all protected
// routes will require a valid token.
router.beforeEach((to) => {
  const requiresAuth = to.meta.requiresAuth && import.meta.env.VITE_REQUIRE_AUTH === 'true'
  if (requiresAuth && !authStore.token) return '/login'
})

export default router
