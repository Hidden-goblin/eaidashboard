// frontend/src/composables/useApiBaseUrl.js
export function useApiBaseUrl() {
    const apiBaseUrl: string = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;
    return apiBaseUrl;
  }
