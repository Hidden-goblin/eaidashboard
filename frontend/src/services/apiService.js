import { useAuthStore } from '../stores/authStore';
import { useApiBaseUrl } from '../composables/useApiBaseUrl'; // Import the new composable

let determinedBaseUrl;

// Vite environment variables are accessed via import.meta.env
const viteApiBaseUrl = import.meta.env.VITE_API_BASE_URL;

if (viteApiBaseUrl && (viteApiBaseUrl.startsWith('http://') || viteApiBaseUrl.startsWith('https://'))) {
  // 1. Use VITE_API_BASE_URL if it's an absolute URL
  determinedBaseUrl = viteApiBaseUrl;
} else if (viteApiBaseUrl && viteApiBaseUrl.trim() !== '' && viteApiBaseUrl !== '/api') {
  // 2. Use VITE_API_BASE_URL if it's a relative path (and not empty or the old default '/api')
  //    The old default '/api' might be from a previous version of .env setup, so we want to prioritize useApiBaseUrl if VITE_API_BASE_URL is just '/api'
  determinedBaseUrl = viteApiBaseUrl;
} else {
  // 3. Fallback to dynamic same-host URL from composable
  // This call is at the module scope. It should be fine as window object is available
  // when this module is imported and used in a browser environment.
  try {
    determinedBaseUrl = useApiBaseUrl();
  } catch (e) {
    // Fallback if useApiBaseUrl fails (e.g. window not defined in some test/SSR context without proper mocking)
    console.error("Error using useApiBaseUrl, falling back to relative /api/v1. Ensure 'window' is defined or VITE_API_BASE_URL is set.", e);
    determinedBaseUrl = '/api/v1'; // Default relative path if composable fails
  }
}

// Remove trailing slash if any, for consistency
const BASE_URL = determinedBaseUrl.replace(/\/$/, '');

// console.log("Determined API BASE_URL:", BASE_URL); // For debugging

export default {
  async get(endpoint, config = {}) {
    const authStore = useAuthStore();
    const token = authStore.getToken; // Assumes getToken is a getter in authStore

    const headers = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: headers,
      ...config.fetchOptions
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API GET request to ${endpoint} failed with status ${response.status}`);
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null;
    }
    return response.json();
  },

  async post(endpoint, data, config = {}) {
    const authStore = useAuthStore();
    const token = authStore.getToken;

    const isFormData = data instanceof FormData;
    const defaultContentTypeHeader = isFormData ? {} : { 'Content-Type': 'application/json' };

    const headers = {
      ...defaultContentTypeHeader,
      ...config.headers,
    };
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const body = isFormData ? data : JSON.stringify(data);

    // When using FormData with fetch, Content-Type header should not be set manually.
    // The browser will set it with the correct boundary.
    if (isFormData) {
      delete headers['Content-Type'];
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: headers,
      body: body,
      ...config.fetchOptions
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API POST request to ${endpoint} failed with status ${response.status}`);
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null;
    }
    return response.json();
  },

  async put(endpoint, data, config = {}) {
    const authStore = useAuthStore();
    const token = authStore.getToken;

    const isFormData = data instanceof FormData;
    const defaultContentTypeHeader = isFormData ? {} : { 'Content-Type': 'application/json' };

    const headers = {
      ...defaultContentTypeHeader,
      ...config.headers,
    };
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const body = isFormData ? data : JSON.stringify(data);

    if (isFormData) {
      delete headers['Content-Type'];
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: headers,
      body: body,
      ...config.fetchOptions
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API PUT request to ${endpoint} failed with status ${response.status}`);
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null;
    }
    return response.json();
  },

  async delete(endpoint, config = {}) {
    const authStore = useAuthStore();
    const token = authStore.getToken;

    const headers = {
      // 'Content-Type': 'application/json', // Usually not needed for DELETE if no body
      ...config.headers,
    };
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: headers,
      ...config.fetchOptions
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API DELETE request to ${endpoint} failed with status ${response.status}`);
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null;
    }
    return response.json();
  }
};
