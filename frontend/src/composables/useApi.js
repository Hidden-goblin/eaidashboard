import { useAuthStore } from "../stores/authStore";

// Global request queue to store failed requests
const requestQueue = [];

export function useApi() {
  const authStore = useAuthStore();

  async function fetchWithAuth(url, options = {}) {
    // const headers = {
    //   "Content-Type": "application/json",
    //   Authorization: `Bearer ${authStore.token}`,
    //   ...options.headers, // Merge additional headers
    // };

    try {
      const response = await fetch(url,  options );

      if (response.status === 401) {
        // 🔥 Unauthorized: Show login modal & queue request for retry
        authStore.showLoginModal = true;
        return new Promise((resolve, reject) => {
          requestQueue.push({ url, options, resolve, reject });
        });
      }
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "API Error");
      }

      return response;
    } catch (error) {
      console.error("API Request Failed:", error);
      throw error;
    }
  }

  function retryRequests(newToken) {
    while (requestQueue.length > 0) {
      const { url, options, resolve, reject } = requestQueue.shift();
      options.headers.Authorization = `Bearer ${newToken}`;
      fetchWithAuth(url, options).then(resolve).catch(reject);
    }
  }

  return { fetchWithAuth, retryRequests };
}
