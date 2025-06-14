import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import LoginView from '../LoginView.vue';
import { useAuthStore } from '../../stores/authStore';
import { createRouter, createWebHistory, START_LOCATION } from 'vue-router';

// Minimal router setup for testing components using <router-link> or useRoute/useRouter
const createTestRouter = () => createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
        { path: '/login', name: 'login', component: LoginView }
        // Add other routes if LoginView navigates to them or if they are needed for context
    ],
});

describe('LoginView.vue', () => {
  let router;

  beforeEach(async () => {
    setActivePinia(createPinia()); // Create a new Pinia instance for each test
    router = createTestRouter();
    // Ensure router is ready before each test, especially if navigation occurs
    // For components not immediately navigating, this might be optional,
    // but good practice if useRoute or router-link is involved.
    router.push('/login'); // Navigate to a starting route if needed, or use START_LOCATION
    await router.isReady();
  });

  it('renders login form correctly', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router] // Provide router to the component
      }
    });
    expect(wrapper.find('h2').text()).toBe('Login');
    expect(wrapper.find('input#username').exists()).toBe(true);
    expect(wrapper.find('input#password').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('calls login action on form submission and redirects on success', async () => {
    const authStore = useAuthStore();

    // Mock the login action
    const loginMock = vi.fn(async (credentials) => {
        // Simulate successful login by updating store state as the action would
        authStore.user = { username: credentials.username, isAdmin: false }; // Mock user data
        authStore.isAuthenticated = true;
        authStore.error = null;
        return Promise.resolve();
    });
    authStore.login = loginMock; // Assign mock to the store instance

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router]
      }
    });

    // Spy on router.push
    const routerPushSpy = vi.spyOn(router, 'push');

    await wrapper.find('input#username').setValue('testuser');
    await wrapper.find('input#password').setValue('password');
    await wrapper.find('form').trigger('submit.prevent');

    expect(loginMock).toHaveBeenCalledTimes(1);
    expect(loginMock).toHaveBeenCalledWith({ username: 'testuser', password: 'password' });

    // Check for redirection (assuming login is successful)
    // This requires the router to have processed the navigation
    // await wrapper.vm.$nextTick(); // Wait for Vue to update
    // await new Promise(resolve => setTimeout(resolve,0)); // allow microtasks/router navigation to complete

    expect(routerPushSpy).toHaveBeenCalledWith('/'); // Default redirect path in LoginView
  });

  it('displays error message on login failure', async () => {
    const authStore = useAuthStore();
    const loginMock = vi.fn(async () => {
        authStore.error = 'Invalid credentials test';
        authStore.isAuthenticated = false; // Ensure not authenticated
        // No need to throw error from mock if component reacts to store.error
    });
    authStore.login = loginMock;

    const wrapper = mount(LoginView, {
        global: {
            plugins: [router]
        }
    });

    await wrapper.find('input#username').setValue('wronguser');
    await wrapper.find('input#password').setValue('wrongpass');
    await wrapper.find('form').trigger('submit.prevent');

    expect(loginMock).toHaveBeenCalledTimes(1);

    await wrapper.vm.$nextTick(); // Wait for reactivity to update DOM

    const errorMessage = wrapper.find('.error-message');
    expect(errorMessage.exists()).toBe(true);
    expect(errorMessage.text()).toBe('Invalid credentials test');
  });
});
