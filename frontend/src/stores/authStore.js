import { defineStore } from 'pinia';
import authService from '../services/authService';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: authService.isAuthenticated(),
    user: null // Or some initial user data
  }),
  getters: {
    getToken: () => authService.getToken()
  },
  actions: {
    async login(credentials) {
      // Call authService.login and update state
      // For now, just simulate
      this.isAuthenticated = true;
      // In a real app, you'd get user data from the login response
      this.user = { username: credentials.username };
    },
    logout() {
      authService.logout();
      this.isAuthenticated = false;
      this.user = null;
    },
    checkAuth() {
       this.isAuthenticated = authService.isAuthenticated();
       // Potentially fetch user profile if authenticated
    }
  }
});
