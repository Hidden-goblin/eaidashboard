import {useAuthStore} from "@/stores/authStore";
import {logger} from "./logger";
import {storeToRefs} from "pinia";
import {useApiBaseUrl} from '@/composables/useApiBaseUrl'
import {reactive} from 'vue'
import {useAuthEvents} from "@/composables/useAuthEvents";


// Define types for fetch options and queued request
type RequestOptions = RequestInit & {
    headers: Record<string, string>; // Required to allow Authorization mutation
};

type QueuedRequest = {
    url: RequestInfo;
    options: RequestOptions;
    resolve: (value: Response | PromiseLike<Response>) => void;
    reject: (reason?: any) => void;
};

const requestQueue = reactive({
    queued: [] as QueuedRequest[],
});

export function useApi() {
    const {emitUnauthorized} = useAuthEvents();
    const apiBaseUrl = useApiBaseUrl();

    /**
     * Process a request automatically adding token from the authStore - call the loginModal if the response is 401 and retry the request
     * @param input : RequestInfo - endpoint
     * @param options : RequestOptions - options usually are {method: (GET|POST|PUT|DELETE), headers: {content-type: <string>}, body: Object}
     * @throws Error - API error message as exception message
     */
    async function fetchWithAuth(input: RequestInfo, options: RequestOptions = {headers: {}}) {
        const url = typeof input === 'string' && input.startsWith('/') ? `${apiBaseUrl}${input}` : input;
        try {
            options = {...options, credentials: 'include'};
            const response = await fetch(url, options);

            if (response.status === 401) {
                emitUnauthorized();
                logger.debug(`401 detected - emitting unauthorized event`);

                return new Promise<Response>((resolve, reject) => {
                    requestQueue.queued.push({url, options, resolve, reject});
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

    async function retryRequests(newToken?: string): Promise<void> {
        const queued = requestQueue.queued.splice(0)
        for (const req of queued) {
            try {
                const init = {...(req.options || {})}
                init.headers = {...(init.headers || {})}
                if (newToken) {
                    init.headers['Authorization'] = `Bearer ${newToken}`
                }
                init.credentials = 'include'
                const res = await fetch(req.url, init)
                if (res.status === 401) {
                    req.reject(new Error('Unauthorized after retry'))
                } else {
                    req.resolve(res)
                }
            } catch (err) {
                req.reject(err)
            }
        }
    }


    return {fetchWithAuth, retryRequests};
}
