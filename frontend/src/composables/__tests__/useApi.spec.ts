import { setActivePinia, createPinia, storeToRefs } from 'pinia'
import { describe, it, expect, vi, beforeEach, beforeAll, afterEach, afterAll } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/node'
import { waitFor } from '@testing-library/vue'
import { ref } from 'vue'

// showLoginModal is exposed by the mocked useAuthEvents so tests can assert UI state
const showLoginModal = ref(false)

// Mock useAuthEvents before importing useApi so the module uses the mock
vi.mock('@/composables/useAuthEvents', () => {
    return {
        useAuthEvents: () => ({
            emitUnauthorized: () => {
                showLoginModal.value = true
            }
        })
    }
})

import { useApi } from '@/composables/useApi'
import { logger } from '@/composables/logger'

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
        showLoginModal.value = false
    })

    it('returns successful response with valid token', async () => {
        const { fetchWithAuth } = useApi()
        const res = await fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            headers: { Authorization: 'Bearer valid.token' }
        })

        const data = await res.json()
        expect(res.status).toBe(200)
        expect(data).toEqual(['project1', 'project2'])
    })

    it('throws error on 403 response and logs it', async () => {
        const { fetchWithAuth } = useApi()
        // Pass a token that the mock server treats as forbidden
        const fetch = fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            headers: { Authorization: 'Bearer not.allowed.token' }
        })
        await expect(fetch).rejects.toThrow('Access denied')
    })

    it('sets showLoginModal to true and queues retry on 401 Unauthorized', async () => {
        const { fetchWithAuth, retryRequests } = useApi()

        // Submit initial request that will be queued (server responds 401 for this token)
        const requestPromise = fetchWithAuth('http://mock-api/api/v1/settings/projects', {
            method: 'GET',
            headers: {
                Authorization: 'Bearer unauthorized.token'
            }
        })

        // The mocked emitUnauthorized should set our ref
        await waitFor(() => {
            expect(showLoginModal.value).toBe(true)
        })

        // Simulate login and retry with a valid token
        retryRequests('valid.token')

        const res = await requestPromise
        const data = await res.json()

        expect(data).toEqual(['project1', 'project2'])
    })

    it('logs and throws on server 500 error', async () => {
        server.use(
            http.get('http://mock-api/api/v1/settings/projects', async () => {
                return HttpResponse.json(null, { status: 500 })
            })
        )
        const originalLoggerError = logger.error
        const loggerErrorSpy = vi.spyOn(logger, 'error').mockImplementation((...args) => {
            return originalLoggerError(...args)
        })

        const { fetchWithAuth } = useApi()

        await expect(
            fetchWithAuth('http://mock-api/api/v1/settings/projects')
        ).rejects.toThrow()

        expect(loggerErrorSpy).toHaveBeenCalled()
    })

    it('queues multiple requests and retries them in order', async () => {
        const { fetchWithAuth, retryRequests } = useApi()

        const p1 = fetchWithAuth('http://mock-api/api/v1/settings/projects')
        const p2 = fetchWithAuth('http://mock-api/api/v1/settings/projects')

        // The mocked emitUnauthorized should set our ref
        await waitFor(() => {
            expect(showLoginModal.value).toBe(true)
        })

        retryRequests('valid.token')

        const [res1, res2] = await Promise.all([p1, p2])
        const [data1, data2] = await Promise.all([res1.json(), res2.json()])

        expect(data1).toEqual(['project1', 'project2'])
        expect(data2).toEqual(['project1', 'project2'])
    })
})