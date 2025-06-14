import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
// Project views
import ProjectsView from '../views/ProjectsView.vue';
import ProjectCreateView from '../views/ProjectCreateView.vue';
import ProjectDetailView from '../views/ProjectDetailView.vue';
import ProjectVersionsView from '../views/ProjectVersionsView.vue';
import ProjectVersionTicketsView from '../views/ProjectVersionTicketsView.vue';
import ProjectBugsView from '../views/ProjectBugsView.vue';
import ProjectCampaignsView from '../views/ProjectCampaignsView.vue';
import ProjectCampaignBoardView from '../views/ProjectCampaignBoardView.vue';
import ProjectRepositoryView from '../views/ProjectRepositoryView.vue';
// Other main views
import UsersView from '../views/UsersView.vue'
import DocumentationView from '../views/DocumentationView.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView
  },
  {
    path: '/projects',
    name: 'projects',
    component: ProjectsView
  },
  {
    path: '/projects/new',
    name: 'project-create',
    component: ProjectCreateView
  },
  {
    path: '/projects/:id',
    component: ProjectDetailView,
    name: 'project-details-base',
    children: [
      {
        path: '',
        name: 'project-details',
        redirect: to => { return { name: 'project-versions', params: { id: to.params.id } } }
      },
      {
        path: 'versions',
        name: 'project-versions',
        components: { projectContent: ProjectVersionsView }
      },
      {
        path: 'versions/:versionId/tickets',
        name: 'project-version-tickets',
        components: { projectContent: ProjectVersionTicketsView }
      },
      {
        path: 'bugs',
        name: 'project-bugs',
        components: { projectContent: ProjectBugsView }
      },
      {
        path: 'campaigns',
        name: 'project-campaigns',
        components: { projectContent: ProjectCampaignsView }
      },
      {
        path: 'campaigns/:campaignId',
        name: 'project-campaign-board',
        components: { projectContent: ProjectCampaignBoardView }
      },
      {
        path: 'repository',
        name: 'project-repository',
        components: { projectContent: ProjectRepositoryView }
      }
    ]
  },
  {
    path: '/users',
    name: 'users',
    component: UsersView
  },
  {
    path: '/documentation',
    name: 'documentation',
    component: DocumentationView
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
