import {setActivePinia, createPinia} from 'pinia'
import {useAuthStore} from '@/stores/authStore'
import {describe, it, expect, beforeEach, afterEach, vi} from 'vitest'
import {jwtDecode} from 'jwt-decode'
import {server} from '@/mocks/node'
import {http, HttpResponse} from 'msw'

beforeAll(() => server.listen())

afterEach(() => {
    server.resetHandlers()
    vi.clearAllMocks()
    localStorage.clear()
})

afterAll(() => server.close())

vi.mock('@/composables/useApiBaseUrl', () => ({
    useApiBaseUrl: () => 'http://mock-api'
}))

vi.mock('jwt-decode', () => ({
    jwtDecode: vi.fn(() => ({
        username: 'john',
        scopes: {
            '*': 'admin',
            project42: 'admin',
            project1: 'user'
        }
    }))
}))

describe('authStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
    })

    it('initializes with default state', () => {
        const store = useAuthStore()
        expect(store.token).toBe(null)
        expect(store.user).toBe(null)
        expect(store.allProjects).toEqual([])
        expect(store.isAuthenticated).toBe(false)
        expect(store.isSuperAdmin).toBe(false)
    })

    it('login updates token, user and localStorage', () => {
        const store = useAuthStore()
        const fakeToken = 'my.jwt.token'

        store.login(fakeToken)

        expect(store.token).toBe(fakeToken)
        expect(store.user.username).toBe('john')
        expect(localStorage.getItem('jwtToken')).toBe(fakeToken)
        expect(localStorage.getItem('user')).toContain('john')
    })

    it('logout clears state and localStorage', () => {
        const store = useAuthStore()
        store.token = 'abc'
        store.user = {name: 'x'}
        store.allProjects = ['p1']
        localStorage.setItem('jwtToken', 'abc')
        localStorage.setItem('user', '{}')
        localStorage.setItem('allProjects', '[]')

        store.logout()

        expect(store.token).toBe(null)
        expect(store.user).toBe(null)
        expect(store.allProjects).toEqual([])
        expect(localStorage.getItem('jwtToken')).toBe(null)
        expect(localStorage.getItem('user')).toBe(null)
    })

    it('filteredProjects returns all if super admin', () => {
        const store = useAuthStore()
        store.login('super.token')
        store.allProjects = ['project1', 'project2']

        expect(store.filteredProjects).toEqual(['project1', 'project2'])
    })

    it('filteredProjects returns scoped projects if not super admin', () => {
        (jwtDecode as any).mockReturnValueOnce({
            username: 'john',
            scopes: {
                projectA: 'user',
                projectB: 'admin'
            }
        })

        const store = useAuthStore()
        store.login('some.token')
        store.allProjects = ['projectA', 'projectB', 'projectC']

        expect(store.filteredProjects).toEqual(['projectA', 'projectB'])
    })

    it('isAdminForProject returns true if user is admin for project', () => {
        const store = useAuthStore()
        store.login('super.token')

        expect(store.isAdminForProject('project42')).toBe(true)
        expect(store.isAdminForProject('project1')).toBe(false)
    })

    it('fetchProjects updates allProjects and localStorage', async () => {
        const store = useAuthStore()
        store.token = 'valid.token'

        await store.fetchProjects()
        console.log("Form the test", store.allProjects)
        expect(store.allProjects).toEqual(['project1', 'project2'])
        expect(localStorage.getItem('allProjects')).toContain('project1')
    })

    it('decodeToken updates user if token exists', () => {
        const store = useAuthStore()
        store.token = 'some.token'
        store.decodeToken()

        expect(store.user.username).toBe('john')
    })

    it('decodeToken sets user to null if token is null', () => {
        const store = useAuthStore()
        store.token = null
        store.decodeToken()

        expect(store.user).toBe(null)
    })

    it('fetchProjects handles API errors and clears allProjects', async () => {

        const store = useAuthStore()
        store.token = 'bad.token'

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
        store.token = 'valid.token'

        await store.fetchProjects()

        expect(store.allProjects).toEqual([])
    })

    it('getUserProjects returns [] when user has no scopes', () => {
        const store = useAuthStore()
        store.user = {username: 'test', scopes: {}}

        expect(store.getUserProjects).toEqual([])
    })

    it('isAdminForProject returns false when user is undefined or missing project', () => {
        const store = useAuthStore()
        store.user = null
        expect(store.isAdminForProject('project1')).toBe(false)

        store.user = {scopes: {project2: 'user'}}
        expect(store.isAdminForProject('project1')).toBe(false)
    })

    it('login handles malformed token (jwtDecode throws)', () => {
        const store = useAuthStore()

        ;(jwtDecode as any).mockImplementationOnce(() => {
            throw new Error('Invalid token')
        })

        expect(() => store.login('bad.token')).toThrow('Invalid token')
    })
})
