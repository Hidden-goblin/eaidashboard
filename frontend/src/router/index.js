import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/authStore';

// View components
import DashboardView from '../views/DashboardView.vue'
import ProjectsView from '../views/ProjectsView.vue';
import ProjectCreateView from '../views/ProjectCreateView.vue';
import ProjectDetailView from '../views/ProjectDetailView.vue';
// ProjectDetailView children (rendered in its <router-view name="projectContent">)
import ProjectVersionsView from '../views/ProjectVersionsView.vue';
import ProjectVersionTicketsView from '../views/ProjectVersionTicketsView.vue';
import ProjectBugsView from '../views/ProjectBugsView.vue';
import ProjectCampaignsView from '../views/ProjectCampaignsView.vue';
import ProjectCampaignBoardView from '../views/ProjectCampaignBoardView.vue';
import ProjectRepositoryView from '../views/ProjectRepositoryView.vue';

import UsersView from '../views/UsersView.vue'
import DocumentationView from '../views/DocumentationView.vue'
import LoginView from '../views/LoginView.vue'; // Import LoginView

// Route guard helpers
const requireAuth = async (to, from, next) => {
  const authStore = useAuthStore();
  // If auth state hasn't been checked yet (e.g., on page refresh)
  if (authStore.user === null && authService.getToken()) { // authService needs to be imported if used here
    await authStore.checkAuth(); // Wait for auth check to complete
  }
  if (!authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } });
  } else {
    next();
  }
};

const requireAdmin = async (to, from, next) => {
  const authStore = useAuthStore();
  if (authStore.user === null && authService.getToken()) { // authService needs to be imported if used here
    await authStore.checkAuth();
  }
  if (!authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } });
  } else if (!authStore.user?.isAdmin) {
    // Redirect to a 'Not Authorized' page or dashboard
    console.warn('Admin access denied, redirecting to dashboard.');
    next({ name: 'dashboard' });
  } else {
    next();
  }
};
// Temporary: Define authService for guards until a better solution for store/service access in guards is found
// This is not ideal. Better would be to ensure authStore is initialized before router guards run.
const authService = { getToken: () => localStorage.getItem('authToken') };


const routes = [
  { path: '/login', name: 'login', component: LoginView },
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/projects', name: 'projects', component: ProjectsView, beforeEnter: requireAuth },
  {
    path: '/projects/new',
    name: 'project-create',
    component: ProjectCreateView,
    beforeEnter: requireAdmin // Example: Only admins can create projects
  },
  {
    path: '/projects/:id',
    component: ProjectDetailView,
    name: 'project-details-base',
    beforeEnter: requireAuth,
    children: [
      { path: '', name: 'project-details', redirect: to => ({ name: 'project-versions', params: { id: to.params.id }})},
      { path: 'versions', name: 'project-versions', components: { projectContent: ProjectVersionsView }},
      { path: 'versions/:versionId/tickets', name: 'project-version-tickets', components: { projectContent: ProjectVersionTicketsView }},
      { path: 'bugs', name: 'project-bugs', components: { projectContent: ProjectBugsView }},
      { path: 'campaigns', name: 'project-campaigns', components: { projectContent: ProjectCampaignsView }},
      { path: 'campaigns/:campaignId', name: 'project-campaign-board', components: { projectContent: ProjectCampaignBoardView }},
      { path: 'repository', name: 'project-repository', components: { projectContent: ProjectRepositoryView }}
    ]
  },
  { path: '/users', name: 'users', component: UsersView, beforeEnter: requireAdmin },
  { path: '/documentation', name: 'documentation', component: DocumentationView, beforeEnter: requireAuth }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

// Global navigation guard (optional, can be useful for initial auth check)
// router.beforeEach(async (to, from, next) => {
//   const authStore = useAuthStore();
//   // Ensure checkAuth is called, especially if not handled in App.vue or individual guards robustly
//   if (!authStore.isAuthenticated && authService.getToken()) {
//     await authStore.checkAuth();
//   }
//   next();
// });

export default router;
