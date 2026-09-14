import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import RegisterStudent from '../views/RegisterStudent.vue'
import RegisterCompany from '../views/RegisterCompany.vue'
import StudentDashboard from '../views/StudentDashboard.vue'
import CompanyDashboard from '../views/CompanyDashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'login', component: Login },
    { path: '/register/student', name: 'register-student', component: RegisterStudent },
    { path: '/register/company', name: 'register-company', component: RegisterCompany },
    {
      path: '/student/dashboard',
      name: 'student-dashboard',
      component: StudentDashboard,
      meta: { requiresAuth: true, role: 'student' }
    },
    {
      path: '/company/dashboard',
      name: 'company-dashboard',
      component: CompanyDashboard,
      meta: { requiresAuth: true, role: 'company' }
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboard,
      meta: { requiresAuth: true, role: 'admin' }
    },
  ],
})

// This runs before EVERY navigation attempt, for every route.
router.beforeEach((to) => {
  const token = sessionStorage.getItem('token')
  const role = sessionStorage.getItem('role')

  if (to.meta.requiresAuth) {
    if (!token) return { name: 'login' }
    if (to.meta.role !== role) return { name: 'login' }
  }
  return true
})

export default router