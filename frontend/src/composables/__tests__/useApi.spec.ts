import {setActivePinia, createPinia, storeToRefs} from 'pinia'
import {describe, it, expect, vi, beforeEach} from 'vitest'
import {http, HttpResponse} from 'msw'
import {server} from '@/mocks/node'
import {useApi} from '@/composables/useApi'
import {waitFor} from '@testing-library/vue'

// Mock the Composition API-style auth store
// vi.mock('@/stores/authStore', () => ({
//     useAuthStore: vi.fn()
// }))


import {useAuthStore} from '@/stores/authStore'
import {logger} from '@/composables/logger'

beforeAll(() => server.listen())
afterEach(() => {
    server.resetHandlers()
    vi.clearAllMocks()
    localStorage.clear()
})
afterAll(() => server.close())

describe('useApi composable', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
    })
    it('returns successful response with valid token', async () => {
        const {fetchWithAuth} = useApi()
        const res = await fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            headers: {Authorization: 'Bearer valid.token'}
        })

        const data = await res.json()
        expect(res.status).toBe(200)
        expect(data).toEqual(['project1', 'project2'])
    })

    it('throws error on 403 response and logs it', async () => {
        //Prepare
        const authStore = useAuthStore();
        const {token} = storeToRefs(authStore);
        token.value = 'not.allowed.token';
        //Execute
        const {fetchWithAuth} = useApi()
        const fetch = fetchWithAuth('http://mock-api/api/v1/settings/projects')
        //Control
        await expect(fetch).rejects.toThrow('Access denied')
    })

    it('sets showLoginModal to true and queues retry on 401 Unauthorized', async () => {
        // Call the store
        const authStore = useAuthStore();
        // destructive access to the reactive property of authStore showLoginModal
        const {showLoginModal} = storeToRefs(authStore);

        const {fetchWithAuth, retryRequests} = useApi()

        // Submit initial request that will be queued
        const requestPromise = fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            method: 'GET',
            headers: {
                Authorization: 'Bearer unauthorized.token'
            }
        })

        // ✅ The modal is triggered
        await waitFor(() => {
            expect(showLoginModal.value).toBe(true);
        });


        // Simulate login and retry with a valid token
        retryRequests('valid.token')

        const res = await requestPromise
        const data = await res.json()

        expect(data).toEqual(['project1', 'project2'])
    })

    it('logs and throws on server 500 error', async () => {
        server.use(
            http.get('http://mock-api/api/v1/settings/projects', async () => {
                    return HttpResponse.json(null, {status: 500})
                }
            )
        )
        const originalLoggerError = logger.error
        const loggerErrorSpy = vi.spyOn(logger, 'error').mockImplementation((...args) => {
            return originalLoggerError(...args)
        })

        const {fetchWithAuth} = useApi()

        await expect(fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            headers: {Authorization: 'Bearer valid.token'}
        })).rejects.toThrow()

        expect(loggerErrorSpy).toHaveBeenCalled()
    })

    it('queues multiple requests and retries them in order', async () => {
        // Call the store
        const authStore = useAuthStore();
        // destructive access to the reactive property of authStore showLoginModal
        const {showLoginModal} = storeToRefs(authStore);

        const {fetchWithAuth, retryRequests} = useApi()

        const p1 = fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            headers: {Authorization: 'Bearer unauthorized.token'}
        })
        const p2 = fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            headers: {Authorization: 'Bearer unauthorized.token'}
        })

        // All requests should be queued
        await waitFor(() => {
            expect(showLoginModal.value).toBe(true);
        })


        retryRequests('valid.token')

        const [res1, res2] = await Promise.all([p1, p2])
        const [data1, data2] = await Promise.all([res1.json(), res2.json()])

        expect(data1).toEqual(['project1', 'project2'])
        expect(data2).toEqual(['project1', 'project2'])
    })
})
