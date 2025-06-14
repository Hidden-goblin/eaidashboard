import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '../authStore';
import authService from '../../services/authService';

// Mock the entire authService
vi.mock('../../services/authService', () => ({
  default: {
    // login: vi.fn(), // login is not directly called by store action in this version
    storeToken: vi.fn(),
    getToken: vi.fn(),
    logout: vi.fn(),
    // isAuthenticated is not directly used by store actions, but by store state init.
    // If needed for initial state testing based on token, mock it too.
    isAuthenticated: vi.fn(() => !!localStorage.getItem('authToken')), // Mock based on LS for consistency
  }
}));

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    // Reset mocks and localStorage before each test
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('initial state is not authenticated', () => {
    // Ensure getToken returns null for a clean initial state test
    authService.getToken.mockReturnValue(null);
    const store = useAuthStore();
    // Trigger checkAuth if it's part of the store's responsibility on creation or if state depends on it
    // For this test, assume initial state is set directly or via a constructor/init pattern not shown
    // The current authStore initializes isAuthenticated to false and user to null by default.
    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
    expect(store.isLoading).toBe(false);
    expect(store.error).toBeNull();
  });

  describe('login action', () => {
    it('successfully authenticates for admin', async () => {
      const store = useAuthStore();
      // No need to mock authService.login if the store's login action has its own logic (as in example)

      await store.login({ username: 'admin', password: 'admin' });

      expect(store.isAuthenticated).toBe(true);
      expect(store.user).toEqual({ username: 'admin', isAdmin: true });
      expect(store.error).toBeNull();
      expect(authService.storeToken).toHaveBeenCalledWith('mock-admin-jwt-token');
      // Or if using localStorage directly in store for this mock:
      // expect(localStorage.getItem('authToken')).toBe('mock-admin-jwt-token');
    });

    it('successfully authenticates for non-admin user', async () => {
      const store = useAuthStore();
      await store.login({ username: 'user', password: 'user' });

      expect(store.isAuthenticated).toBe(true);
      expect(store.user).toEqual({ username: 'user', isAdmin: false });
      expect(authService.storeToken).toHaveBeenCalledWith('mock-user-jwt-token');
    });

    it('handles login failure', async () => {
      const store = useAuthStore();
      await store.login({ username: 'wrong', password: 'user' });

      expect(store.isAuthenticated).toBe(false);
      expect(store.user).toBeNull();
      expect(store.error).toBe('Invalid credentials');
      expect(authService.storeToken).not.toHaveBeenCalled();
    });
  });

  describe('logout action', () => {
    it('clears authentication state', () => {
      const store = useAuthStore();
      // Simulate logged-in state
      store.isAuthenticated = true;
      store.user = { username: 'test', isAdmin: false };
      // authService.storeToken('fake-token'); // Simulate token was stored

      store.logout();

      expect(store.isAuthenticated).toBe(false);
      expect(store.user).toBeNull();
      expect(store.error).toBeNull();
      expect(authService.logout).toHaveBeenCalledTimes(1);
    });
  });

  describe('checkAuth action', () => {
    it('restores admin state if admin token exists', async () => {
      authService.getToken.mockReturnValue('mock-admin-jwt-token');
      const store = useAuthStore();
      await store.checkAuth();

      expect(store.isAuthenticated).toBe(true);
      expect(store.user).toEqual({ username: 'admin', isAdmin: true });
    });

    it('restores user state if user token exists', async () => {
      authService.getToken.mockReturnValue('mock-user-jwt-token');
      const store = useAuthStore();
      await store.checkAuth();

      expect(store.isAuthenticated).toBe(true);
      expect(store.user).toEqual({ username: 'user', isAdmin: false });
    });

    it('logs out if token is invalid or unknown', async () => {
      authService.getToken.mockReturnValue('invalid-or-unknown-token');
      const store = useAuthStore();
      await store.checkAuth();

      expect(store.isAuthenticated).toBe(false);
      expect(store.user).toBeNull();
      expect(authService.logout).toHaveBeenCalled(); // checkAuth should call logout for invalid tokens
    });

    it('does nothing if no token exists', async () => {
      authService.getToken.mockReturnValue(null);
      const store = useAuthStore();
      await store.checkAuth();

      expect(store.isAuthenticated).toBe(false);
      expect(store.user).toBeNull();
      expect(authService.logout).not.toHaveBeenCalled(); // Logout shouldn't be called if no token
    });
  });

  it('isAdmin getter works correctly', () => {
    const store = useAuthStore();
    expect(store.isAdmin).toBe(false); // Initially null user

    store.user = { username: 'adminUser', isAdmin: true };
    expect(store.isAdmin).toBe(true);

    store.user = { username: 'normalUser', isAdmin: false };
    expect(store.isAdmin).toBe(false);
  });
});
