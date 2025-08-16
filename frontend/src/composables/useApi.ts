import { useAuthStore } from "@/stores/authStore";
import { logger } from "./logger";
import { storeToRefs } from "pinia";

// Define types for fetch options and queued request
type RequestOptions = RequestInit & {
  headers: Record<string, string>; // Required to allow Authorization mutation
};

type QueuedRequest = {
  url: string;
  options: RequestOptions;
  resolve: (value: Response | PromiseLike<Response>) => void;
  reject: (reason?: any) => void;
};

const requestQueue: QueuedRequest[] = [];

export function useApi() {
  const authStore = useAuthStore();
  const { showLoginModal } = storeToRefs(authStore);

    /**
     * Process a request automatically adding token from the authStore - call the loginModal if the response is 401 and retry the request
     * @param url : string - endpoint
     * @param options : RequestOptions - options usually are {method: (GET|POST|PUT|DELETE), headers: {content-type: <string>}, body: Object}
     * @throws Error - API error message as exception message
     */
  async function fetchWithAuth(url: string, options: RequestOptions = { headers: {} }) {
    try {
      options.headers = options.headers || {};
      if (authStore.token) {
        options.headers.Authorization = `Bearer ${authStore.token}`;
      }

      const response = await fetch(url, options);

      if (response.status === 401) {
        showLoginModal.value = true;
        logger.debug(`Show Login Modal is ${showLoginModal.value}`);

        return new Promise<Response>((resolve, reject) => {
          requestQueue.push({ url, options, resolve, reject });
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "API Error");
      }

      return response;
    } catch (error) {
      logger.error(`API Request to ${url} Failed`);
      throw error;
    }
  }

  function retryRequests(newToken: string): void {
    while (requestQueue.length > 0) {
      const { url, options, resolve, reject } = requestQueue.shift()!;
      options.headers.Authorization = `Bearer ${newToken}`;
      fetchWithAuth(url, options).then(resolve).catch(reject);
    }
  }

  return { fetchWithAuth, retryRequests };
}
