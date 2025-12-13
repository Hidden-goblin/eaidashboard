import {setActivePinia, createPinia} from 'pinia'
import {useAuthStore} from '@/stores/authStore'
import {describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll} from 'vitest'
import {InvalidTokenError, jwtDecode} from 'jwt-decode'
import {server} from '@/mocks/node'
import {http, HttpResponse} from 'msw'
import {authStoreHandler} from "@/mocks/authStoreHandler";
import {nextTick} from "vue";

beforeAll(() => server.listen());
afterEach(() => {
    localStorage.clear();
    server.resetHandlers();
});
afterAll(() => server.close());


vi.mock('@/composables/useApiBaseUrl', () => ({
    useApiBaseUrl: () => 'http://mock-api'
}))

vi.mock('@/composables/useApi', () => {
    return {
        useApi: () => ({
            retryRequests: vi.fn(async (_token?: string) => {
            }),
            fetchWithAuth: vi.fn(async (url: string, options?: RequestInit) => {
                return fetch(url, options as any)
            })
        })
    }
})


describe('authStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
    })

    it('initializes with default state', () => {
        const store = useAuthStore()
        expect(store.user).toBe(null)
        expect(store.allProjects).toEqual([])
        expect(store.isAuthenticated).toBe(false)
        expect(store.isSuperAdmin).toBe(false)
    })

    it('login updates user and localStorage', async () => {
        setActivePinia(createPinia())
        server.use(...authStoreHandler)
        const store = useAuthStore()
        const loginString = "username=" + encodeURIComponent('john@jon.son') + '&password=' + encodeURIComponent("password")

        await store.login(loginString)
        await nextTick()

        expect(store.user?.username).toBe('john')
        expect(localStorage.getItem('user')).toContain('john')
    })

    it('logout clears state and localStorage', async () => {
        setActivePinia(createPinia());
        server.use(...authStoreHandler);
        const store = useAuthStore();
        const loginString = "username=" + encodeURIComponent('john@jon.son') + '&password=' + encodeURIComponent("password");
        await store.login(loginString);
        await nextTick()
        store.logout()

        expect(store.user).toBe(null)
        expect(store.allProjects).toEqual([])
        expect(localStorage.getItem('user')).toEqual('null')
        expect(localStorage.getItem('allProjects')).toEqual('[]')
    })

    it('filteredProjects returns all if super admin', async () => {
        setActivePinia(createPinia());
        server.use(...authStoreHandler);
        const store = useAuthStore();
        const loginString = "username=" + encodeURIComponent('john@jon.son') + '&password=' + encodeURIComponent("password");
        await store.login(loginString);
        await nextTick()
        expect(store.filteredProjects).toEqual([ 'project42', 'project1','project10'])
    })

    it('filteredProjects returns scoped projects if not super admin', async () => {
        setActivePinia(createPinia());
        server.use(...authStoreHandler);
        const store = useAuthStore();
        const loginString = "username=" + encodeURIComponent('user@jon.son') + '&password=' + encodeURIComponent("password");
        await store.login(loginString);
        await nextTick()
        expect(store.filteredProjects).toEqual(['project42', 'project1'])
    })

    it('isAdminForProject returns true if user is admin for project', async () => {
        setActivePinia(createPinia());
        server.use(...authStoreHandler);
        const store = useAuthStore();
        const loginString = "username=" + encodeURIComponent('user@jon.son') + '&password=' + encodeURIComponent("password");
        await store.login(loginString);
        await nextTick()
        expect(store.isAdminForProject('project42')).toBe(false)
        expect(store.isAdminForProject('project1')).toBe(true)
    })

    it('fetchProjects updates allProjects and localStorage', async () => {
        setActivePinia(createPinia());
        server.use(...authStoreHandler);
        const store = useAuthStore();
        await store.fetchProjects();
        expect(store.allProjects).toEqual([ 'project42', 'project1','project10'])
        expect(localStorage.getItem('allProjects')).toContain('project1')
    })

    it('fetchProjects handles API errors and clears allProjects', async () => {
        const store = useAuthStore()
        await store.fetchProjects()

        expect(store.allProjects).toEqual([])
    })

    it('fetchProjects handles network failure', async () => {
        server.use(
            http.get('http://mock-api/api/v1/settings/projects', () => {
                return HttpResponse.error()
            })
        )

        const store = useAuthStore()
        await store.fetchProjects()
        expect(store.allProjects).toEqual([])
    })

    it('getUserProjects returns [] when user has no scopes', async () => {
        setActivePinia(createPinia());
        server.use(...authStoreHandler);
        const store = useAuthStore();
        const loginString = "username=" + encodeURIComponent('noscope@jon.son') + '&password=' + encodeURIComponent("password");
        await store.login(loginString);

        expect(store.getUserProjects).toEqual([])
    })

    it('isAdminForProject returns false when user is undefined or missing project', () => {
        setActivePinia(createPinia());
        const store = useAuthStore();

        // user is null
        store.$patch({ user: null });
        expect(store.isAdminForProject('project1')).toBe(false);

        // user exists but has no scopes
        store.$patch({ user: { username: 'noscope' } as any });
        expect(store.isAdminForProject('project1')).toBe(false);

        // user has scopes but not for the tested project
        store.$patch({ user: { scopes: { project2: 'user' } } as any });
        expect(store.isAdminForProject('project1')).toBe(false);
    })

    it('login handles malformed token (jwtDecode throws)', async () => {
        setActivePinia(createPinia());
        server.use(...authStoreHandler);
        const store = useAuthStore();
        const loginString = "username=" + encodeURIComponent('badjwt@jon.son') + '&password=' + encodeURIComponent("password");

        await expect(store.login(loginString)).rejects.toThrow(InvalidTokenError)
    })
})
