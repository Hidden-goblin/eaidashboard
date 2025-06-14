import { defineStore } from 'pinia';
import authService from '../services/authService'; // Assuming authService handles token storage

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null, // Example: { username: 'admin', isAdmin: true }
    isAuthenticated: false,
    isLoading: false, // To track login/auth check process
    error: null,
  }),
  getters: {
    isAdmin: (state) => state.user && state.user.isAdmin,
    // getToken is already in authService, but if needed here:
    // getToken: () => authService.getToken(),
  },
  actions: {
    async login(credentials) {
      this.isLoading = true;
      this.error = null;
      try {
        // In a real app, authService.login would make an API call
        // and return user data including roles and the token.
        // const apiUserData = await authService.login(credentials);

        // Mocking a successful login based on username:
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
        let userDataFromApi;
        if (credentials.username === 'admin' && credentials.password === 'admin') {
          userDataFromApi = {
            username: credentials.username,
            isAdmin: true,
            token: 'mock-admin-jwt-token' // This token should be real in a real app
          };
        } else if (credentials.username === 'user' && credentials.password === 'user') {
          userDataFromApi = {
            username: credentials.username,
            isAdmin: false,
            token: 'mock-user-jwt-token'
          };
        } else {
          throw new Error('Invalid credentials');
        }

        // Store token using authService (which should use localStorage)
        authService.storeToken(userDataFromApi.token); // You'll need to add storeToken to authService.js
                                                     // For now, directly use localStorage if authService is not updated.
                                                     // localStorage.setItem('authToken', userDataFromApi.token);


        this.isAuthenticated = true;
        this.user = { username: userDataFromApi.username, isAdmin: userDataFromApi.isAdmin };
        this.error = null;
      } catch (error) {
        this.isAuthenticated = false;
        this.user = null;
        this.error = error.message || 'Failed to login';
        // Don't throw error here if you want the component to handle UI based on store state
        // throw error;
      } finally {
        this.isLoading = false;
      }
    },

    logout() {
      authService.logout(); // This should clear the token from localStorage
      this.isAuthenticated = false;
      this.user = null;
      this.error = null;
      // Potentially redirect to login page using router if needed globally
    },

    async checkAuth() {
      this.isLoading = true;
      const token = authService.getToken();
      if (token) {
        try {
          // MOCK: In a real app, you'd verify token with backend (e.g. GET /users/me)
          // and get user details including username and isAdmin.
          // For this mock, we'll simulate based on the mock tokens.
          await new Promise(resolve => setTimeout(resolve, 100)); // Simulate API delay
          let mockUser;
          if (token === 'mock-admin-jwt-token') {
            mockUser = { username: 'admin', isAdmin: true };
          } else if (token === 'mock-user-jwt-token') {
            mockUser = { username: 'user', isAdmin: false };
          } else {
            // If token is unknown or invalid in this mock setup
            this.logout(); // Clears invalid token
            this.isLoading = false;
            return;
          }
          this.user = mockUser;
          this.isAuthenticated = true;
        } catch (e) {
          console.error("checkAuth error:", e)
          this.logout(); // Token validation failed or other error
        }
      } else {
        this.isAuthenticated = false;
        this.user = null;
      }
      this.isLoading = false;
    }
  }
});
