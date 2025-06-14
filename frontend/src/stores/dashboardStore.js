import { defineStore } from 'pinia';
import apiService from '../services/apiService'; // Import the apiService

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    projects: [],
    isLoading: false,
    error: null
  }),
  actions: {
    async fetchDashboardData() {
      this.isLoading = true;
      this.error = null;
      try {
        // Use the actual API endpoint for dashboard data
        // This endpoint needs to be defined in the backend (e.g., app.routers.rest.*)
        // Assuming an endpoint like '/dashboard' or '/projects-summary'
        const data = await apiService.get('/dashboard'); // Adjust endpoint as needed
        this.projects = data.projects; // Assuming the API returns { projects: [...] }
      } catch (e) {
        this.error = e.message || 'Failed to fetch dashboard data.';
        console.error(e);
        // Keep mock data for fallback if API fails during development
        this.projects = [
          {
            name: 'Project Alpha (Fallback)',
            versions: [
              { version: '1.0.0', status: 'Error fetching data', tickets: 0, bugs: 0 }
            ]
          },
          {
            name: 'Project Beta (Fallback)',
            versions: [
              { version: '2.0.0', status: 'Error fetching data', tickets: 0, bugs: 0 }
            ]
          }
        ];
      } finally {
        this.isLoading = false;
      }
    }
  }
});
