import { defineStore } from 'pinia';
import apiService from '../services/apiService';

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [],
    currentProject: null,
    isLoading: false,
    isVersionsLoading: false,
    error: null,
    versionsError: null,
    currentVersionTickets: [],
    isTicketsLoading: false,
    ticketsError: null,
    projectBugs: [],
    isBugsLoading: false,
    bugsError: null,
    projectCampaigns: [],
    currentCampaign: null,
    isCampaignsLoading: false,
    campaignsError: null,
    // New state for repository
    projectRepositoryEpics: [],
    projectRepositoryFeatures: [], // Features for a selected epic
    projectRepositoryScenarios: [], // Scenarios for a selected feature
    isRepositoryLoading: false,
    repositoryError: null,
  }),
  actions: {
    // --- Existing Project Actions ---
    async fetchProjects() {
      this.isLoading = true; this.error = null;
      try { const data = await apiService.get('/projects'); this.projects = data.projects || data; }
      catch (e) { this.error = e.message || 'Failed to fetch projects.'; console.error(e); this.projects = []; }
      finally { this.isLoading = false; }
    },
    async fetchProjectDetails(projectId) {
      this.isLoading = true; this.error = null;
      if (!this.currentProject || this.currentProject.id !== projectId) this.currentProject = null;
      try {
        const data = await apiService.get(`/projects/${projectId}`);
        const existingVersions = this.currentProject?.versions || [];
        this.currentProject = { ...data, versions: data.versions || existingVersions || [] };
      } catch (e) { this.error = e.message || `Failed to fetch project ${projectId}.`; console.error(e); this.currentProject = null; }
      finally { this.isLoading = false; }
    },
    async createProject(projectData) {
      this.isLoading = true; this.error = null;
      try { const newProject = await apiService.post('/projects', projectData); this.projects.push(newProject); return newProject; }
      catch (e) { this.error = e.message || 'Failed to create project.'; console.error(e); throw e; }
      finally { this.isLoading = false; }
    },

    // --- Existing Version Actions ---
    async fetchProjectVersions(projectId, forceRefresh = false) {
      if (this.currentProject?.id === projectId && this.currentProject.versions?.length > 0 && !forceRefresh) return;
      this.isVersionsLoading = true; this.versionsError = null;
      try {
        const data = await apiService.get(`/projects/${projectId}/versions`);
        if (this.currentProject?.id === projectId) this.currentProject.versions = data.versions || data;
      } catch (e) { this.versionsError = e.message || `Failed to fetch versions for project ${projectId}.`; console.error(e); if (this.currentProject?.id === projectId) this.currentProject.versions = []; }
      finally { this.isVersionsLoading = false; }
    },
    async createProjectVersion(projectId, versionData) {
      this.isVersionsLoading = true; this.versionsError = null;
      try {
        const newVersion = await apiService.post(`/projects/${projectId}/versions`, versionData);
        if (this.currentProject?.id === projectId) {
          if (!this.currentProject.versions) this.currentProject.versions = [];
          this.currentProject.versions.push(newVersion);
        }
        const projectInList = this.projects.find(p => p.id === projectId);
        if (projectInList) {
          if (!projectInList.versions) projectInList.versions = [];
          if (!projectInList.versions.find(v => v.id === newVersion.id)) projectInList.versions.push(newVersion);
        }
        return newVersion;
      } catch (e) { this.versionsError = e.message || 'Failed to create version.'; console.error(e); throw e; }
      finally { this.isVersionsLoading = false; }
    },

    // --- Existing Ticket Actions ---
    async fetchTicketsForVersion(projectId, versionId) {
      this.isTicketsLoading = true; this.ticketsError = null; this.currentVersionTickets = [];
      try {
        const data = await apiService.get(`/projects/${projectId}/versions/${versionId}/tickets`);
        this.currentVersionTickets = data.tickets || data;
      } catch (e) { this.ticketsError = e.message || `Failed to fetch tickets for version ${versionId}.`; console.error(e); this.currentVersionTickets = []; }
      finally { this.isTicketsLoading = false; }
    },
    async createTicketInVersion(projectId, versionId, ticketData) {
      this.isTicketsLoading = true; this.ticketsError = null;
      try {
        const newTicket = await apiService.post(`/projects/${projectId}/versions/${versionId}/tickets`, ticketData);
        this.currentVersionTickets.push(newTicket); return newTicket;
      } catch (e) { this.ticketsError = e.message || 'Failed to create ticket.'; console.error(e); throw e; }
      finally { this.isTicketsLoading = false; }
    },
    async updateTicket(projectId, versionId, ticketId, ticketData) {
      this.isTicketsLoading = true; this.ticketsError = null;
      try {
        const updatedTicket = await apiService.put(`/projects/${projectId}/versions/${versionId}/tickets/${ticketId}`, ticketData);
        const index = this.currentVersionTickets.findIndex(t => t.id === ticketId);
        if (index !== -1) this.currentVersionTickets.splice(index, 1, updatedTicket);
        return updatedTicket;
      } catch (e) { this.ticketsError = e.message || `Failed to update ticket ${ticketId}.`; console.error(e); throw e; }
      finally { this.isTicketsLoading = false; }
    },

    // --- Existing Bug Actions ---
    async fetchBugsForProject(projectId, filters = {}) {
      this.isBugsLoading = true; this.bugsError = null; this.projectBugs = [];
      try {
        let endpoint = `/projects/${projectId}/bugs`;
        const queryParams = new URLSearchParams(filters).toString();
        if (queryParams) endpoint += `?${queryParams}`;
        const data = await apiService.get(endpoint); this.projectBugs = data.bugs || data;
      } catch (e) { this.bugsError = e.message || `Failed to fetch bugs for project ${projectId}.`; console.error(e); this.projectBugs = []; }
      finally { this.isBugsLoading = false; }
    },
    async createBug(projectId, bugData) {
      this.isBugsLoading = true; this.bugsError = null;
      try {
        const newBug = await apiService.post(`/projects/${projectId}/bugs`, bugData);
        this.projectBugs.unshift(newBug); return newBug;
      } catch (e) { this.bugsError = e.message || 'Failed to create bug.'; console.error(e); throw e; }
      finally { this.isBugsLoading = false; }
    },
    async updateBug(projectId, bugId, bugData) {
      this.isBugsLoading = true; this.bugsError = null;
      try {
        const updatedBug = await apiService.put(`/projects/${projectId}/bugs/${bugId}`, bugData);
        const index = this.projectBugs.findIndex(b => b.id === bugId);
        if (index !== -1) this.projectBugs.splice(index, 1, updatedBug);
        return updatedBug;
      } catch (e) { this.bugsError = e.message || `Failed to update bug ${bugId}.`; console.error(e); throw e; }
      finally { this.isBugsLoading = false; }
    },

    // --- Existing Campaign Actions ---
    async fetchCampaignsForProject(projectId, filters = {}) {
      this.isCampaignsLoading = true; this.campaignsError = null; this.projectCampaigns = [];
      try {
        let endpoint = `/projects/${projectId}/campaigns`;
        const queryParams = new URLSearchParams(); if (filters.version) queryParams.append('version', filters.version);
        if (queryParams.toString()) endpoint += `?${queryParams.toString()}`;
        const data = await apiService.get(endpoint); this.projectCampaigns = data.campaigns || data;
      } catch (e) { this.campaignsError = e.message || `Failed to fetch campaigns for project ${projectId}.`; console.error(e); this.projectCampaigns = []; }
      finally { this.isCampaignsLoading = false; }
    },
    async createCampaign(projectId, campaignData) {
      this.isCampaignsLoading = true; this.campaignsError = null;
      try {
        const newCampaign = await apiService.post(`/projects/${projectId}/campaigns`, campaignData);
        this.projectCampaigns.unshift(newCampaign); return newCampaign;
      } catch (e) { this.campaignsError = e.message || 'Failed to create campaign.'; console.error(e); throw e; }
      finally { this.isCampaignsLoading = false; }
    },
    async fetchCampaignDetails(projectId, campaignId) {
      this.isCampaignsLoading = true; this.campaignsError = null; this.currentCampaign = null;
      try {
        const data = await apiService.get(`/projects/${projectId}/campaigns/${campaignId}`); this.currentCampaign = data;
      } catch (e) { this.campaignsError = e.message || `Failed to fetch campaign details for ${campaignId}.`; console.error(e); this.currentCampaign = null; }
      finally { this.isCampaignsLoading = false; }
    },

    // --- New Repository Actions ---
    async fetchEpics(projectId) {
      this.isRepositoryLoading = true;
      this.repositoryError = null;
      try {
        const data = await apiService.get(`/projects/${projectId}/repository/epics`);
        this.projectRepositoryEpics = data.epics || data;
        this.projectRepositoryFeatures = []; // Clear dependent
        this.projectRepositoryScenarios = []; // Clear dependent
      } catch (e) {
        this.repositoryError = e.message || `Failed to fetch epics for project ${projectId}.`;
        this.projectRepositoryEpics = [];
      } finally {
        this.isRepositoryLoading = false;
      }
    },

    async fetchFeatures(projectId, epicId) {
      this.isRepositoryLoading = true;
      this.repositoryError = null;
      try {
        const data = await apiService.get(`/projects/${projectId}/repository/epics/${epicId}/features`);
        this.projectRepositoryFeatures = data.features || data;
        this.projectRepositoryScenarios = []; // Clear dependent
      } catch (e) {
        this.repositoryError = e.message || `Failed to fetch features for epic ${epicId}.`;
        this.projectRepositoryFeatures = [];
      } finally {
        this.isRepositoryLoading = false;
      }
    },

    async fetchScenarios(projectId, epicId, featureId, filters = {}) {
      this.isRepositoryLoading = true;
      this.repositoryError = null;
      try {
        let endpoint = `/projects/${projectId}/repository/epics/${epicId}/features/${featureId}/scenarios`;
        const queryParams = new URLSearchParams();
        if (filters.limit) queryParams.append('limit', filters.limit);
        if (filters.skip) queryParams.append('skip', filters.skip);
        if (queryParams.toString()) endpoint += `?${queryParams.toString()}`;

        const data = await apiService.get(endpoint);
        this.projectRepositoryScenarios = data.scenarios || data;
      } catch (e) {
        this.repositoryError = e.message || `Failed to fetch scenarios for feature ${featureId}.`;
        this.projectRepositoryScenarios = [];
      } finally {
        this.isRepositoryLoading = false;
      }
    },

    async importRepositoryCsv(projectId, file) {
      this.isRepositoryLoading = true;
      this.repositoryError = null;
      try {
        const formData = new FormData();
        formData.append('file', file);
        // Pass the customConfig directly to apiService.post
        await apiService.post(`/projects/${projectId}/repository/import-csv`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        await this.fetchEpics(projectId); // Refresh epics list
      } catch (e) {
        this.repositoryError = e.message || 'Failed to import repository CSV.';
        throw e;
      } finally {
        this.isRepositoryLoading = false;
      }
    }
  }
});
