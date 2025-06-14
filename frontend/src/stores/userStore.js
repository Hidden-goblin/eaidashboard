import { defineStore } from 'pinia';
import apiService from '../services/apiService';

export const useUserStore = defineStore('userManagement', {
  state: () => ({
    users: [],
    isLoading: false,
    error: null,
  }),
  actions: {
    async fetchUsers() {
      this.isLoading = true;
      this.error = null;
      try {
        // Assuming API GET /api/v1/users
        const data = await apiService.get('/users');
        this.users = data.users || data; // Adjust based on API response structure
      } catch (e) {
        this.error = e.message || 'Failed to fetch users.';
        this.users = [];
        console.error("fetchUsers error:", e);
      } finally {
        this.isLoading = false;
      }
    },
    async createUser(userData) {
      this.isLoading = true;
      this.error = null;
      try {
        // API POST /api/v1/users
        const newUser = await apiService.post('/users', userData);
        this.users.push(newUser);
        return newUser;
      } catch (e) {
        this.error = e.message || 'Failed to create user.';
        console.error("createUser error:", e);
        throw e; // Re-throw for component to handle specific feedback if needed
      } finally {
        this.isLoading = false;
      }
    },
    async updateUser(userId, userData) {
      this.isLoading = true;
      this.error = null;
      try {
        // API PUT /api/v1/users/{userId}
        const updatedUser = await apiService.put(`/users/${userId}`, userData);
        const index = this.users.findIndex(u => u.id === userId);
        if (index !== -1) {
          this.users.splice(index, 1, updatedUser);
        }
        return updatedUser;
      } catch (e) {
        this.error = e.message || `Failed to update user ${userId}.`;
        console.error("updateUser error:", e);
        throw e;
      } finally {
        this.isLoading = false;
      }
    },
    async deleteUser(userId) {
      this.isLoading = true;
      this.error = null;
      try {
        // API DELETE /api/v1/users/{userId}
        await apiService.delete(`/users/${userId}`);
        this.users = this.users.filter(u => u.id !== userId);
      } catch (e) {
        this.error = e.message || `Failed to delete user ${userId}.`;
        console.error("deleteUser error:", e);
        throw e;
      } finally {
        this.isLoading = false;
      }
    }
  }
});
