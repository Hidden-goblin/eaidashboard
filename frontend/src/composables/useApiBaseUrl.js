// frontend/src/composables/useApiBaseUrl.js
export function useApiBaseUrl() {
    const apiBaseUrl = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;
    return apiBaseUrl;
  }
