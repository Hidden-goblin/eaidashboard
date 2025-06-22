import { createWebHistory, createRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'
import DashboardView from '../views/DashboardView.vue'; // Assume a Home component exists.
import Administration from '../components/Administration.vue';
import Project from '../components/Project.vue';

const routes = [
  { path: '/', name: 'Home', component: DashboardView },
  { path: '/admin', name: 'Administration', component: Administration, meta: {requiresAuth: true, requiresAdmin: true } },
  { path: '/projects/:projectName', name: 'Project', component: Project, meta: { requiresAuth: true, requiresProjectAccess: true }}
];


const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next('/');
  }

  if (to.meta.requiresAdmin && !authStore.isSuperAdmin) {
    return next('/'); // Redirect unauthorized admins
  }

  if (to.meta.requiresProjectAccess) {
    const projectName = to.params.projectName;
    if (!authStore.isSuperAdmin && !authStore.getUserProjects.includes(projectName)) {
      return next('/'); // Prevent unauthorized project access
    }
  }

  next();
});


export default router
