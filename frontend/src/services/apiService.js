import { useAuthStore } from '../stores/authStore'; // To get tokens

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'; // Configure API base URL

export default {
  async get(endpoint) {
    const authStore = useAuthStore();
    // Access the token via the getter if Pinia version requires .value for getters, or directly if not.
    // Assuming Pinia setup makes getters directly accessible.
    const token = authStore.getToken;

    const headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: headers
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API GET request to ${endpoint} failed with status ${response.status}`);
    }
    // Handle cases where response might be empty but successful (e.g. 204 No Content)
    if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null;
    }
    return response.json();
  },

  async post(endpoint, data, customConfig = {}) {
    const authStore = useAuthStore();
    const token = authStore.getToken;

    // Start with custom headers or default to JSON
    const headers = { ...customConfig.headers };

    // Set default Content-Type if not already set by customConfig (e.g. for FormData)
    if (!headers['Content-Type'] && !(data instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Stringify body if JSON, otherwise pass data as is (for FormData)
    const body = (headers['Content-Type'] === 'application/json' && !(data instanceof FormData))
                 ? JSON.stringify(data)
                 : data;

    // If Content-Type is multipart/form-data, delete it from headers
    // as fetch will set it correctly with the boundary.
    if (data instanceof FormData) {
        delete headers['Content-Type'];
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: headers,
      body: body
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

  async put(endpoint, data, customConfig = {}) {
    const authStore = useAuthStore();
    const token = authStore.getToken;

    const headers = { ...customConfig.headers };
    if (!headers['Content-Type'] && !(data instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const body = (headers['Content-Type'] === 'application/json' && !(data instanceof FormData))
                 ? JSON.stringify(data)
                 : data;

    if (data instanceof FormData) {
        delete headers['Content-Type'];
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: headers,
      body: body
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

  async delete(endpoint) {
    const authStore = useAuthStore();
    const token = authStore.getToken;
    const headers = {
      'Authorization': `Bearer ${token}`
      // No Content-Type needed for typical DELETE requests without a body
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: headers
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API DELETE request to ${endpoint} failed with status ${response.status}`);
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") {
        return null;
    }
    return response.json(); // Or handle differently if DELETE usually returns no content
  }
};
