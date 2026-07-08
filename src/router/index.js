import { createRouter, createWebHashHistory } from "vue-router"
import { isLoggedIn } from "@/lib/apiClient"

const Login = () => import("@/views/rockburst/LoginView.vue")
const Register = () => import("@/views/rockburst/RegisterView.vue")
const Dashboard = () => import("@/views/rockburst/DashboardView.vue")

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/login", component: Login },
    { path: "/register", component: Register },
    { path: "/dashboard", component: Dashboard, meta: { requiresAuth: true } },
    { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
  ],
})

router.beforeEach((to) => {
  const loggedIn = isLoggedIn()
  if ((to.path === "/login" || to.path === "/register") && loggedIn) {
    return "/dashboard"
  }
  if (to.meta.requiresAuth && !loggedIn) {
    return { path: "/login", query: { redirect: to.fullPath } }
  }
  return true
})

export default router
