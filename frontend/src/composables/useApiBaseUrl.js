// frontend/src/composables/useApiBaseUrl.js
export function useApiBaseUrl() {
    // Define the base URL for the API
    // This assumes the API is served from the same hostname as the frontend,
    // but on port 8087.
    const apiBaseUrl = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;
    return apiBaseUrl;
  }
