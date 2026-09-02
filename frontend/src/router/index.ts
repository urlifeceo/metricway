import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import Login from "@/views/Login.vue";
import Dashboard from "@/views/DashboardView.vue";

const routes: RouteRecordRaw[] = [
  { path: "/login", component: Login },
  {
    path: "/",
    component: Dashboard,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();

  if (to.meta.requiresAuth && !auth.token) {
    return "/login";
  }
});

export default router;
