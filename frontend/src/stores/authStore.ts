import { defineStore } from 'pinia'
import { jwtDecode } from 'jwt-decode'
import { useApiBaseUrl } from '@/composables/useApiBaseUrl'
import { ref, computed } from 'vue'
import { useApi } from '@/composables/useApi'
import { logger } from '@/composables/logger'

// -----------------------------
// Interfaces for user & JWT
// -----------------------------
interface User {
    username?: string
    email?: string
    scopes?: Record<string, 'admin' | 'user'>
    [key: string]: any
}

// -----------------------------
// Store definition
// -----------------------------
export const useAuthStore = defineStore('auth', () => {
    // State
    const token = ref<string | null>(localStorage.getItem('jwtToken') || 'null')
    const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))
    const allProjects = ref<string[]>(JSON.parse(localStorage.getItem('allProjects') || '[]'))
    const showLoginModal = ref(false)

    const { retryRequests, fetchWithAuth } = useApi()

    // Getters
    const isAuthenticated = computed(() => !!token.value)

    const isSuperAdmin = computed(() => user.value?.scopes?.['*'] === 'admin')

    const getUserProjects = computed((): string[] =>
        Object.keys(user.value?.scopes || {}).filter((p) => p !== '*')
    )

    const isAdminForProject = (project: string): boolean =>
        user.value?.scopes?.[project] === 'admin'

    const filteredProjects = computed(() =>
        isSuperAdmin.value ? allProjects.value : getUserProjects.value
    )

    // Actions
    function login(newToken: string) {
        token.value = newToken
        localStorage.setItem('jwtToken', newToken)
        user.value = jwtDecode<User>(newToken)
        localStorage.setItem('user', JSON.stringify(user.value))
        showLoginModal.value = false
        retryRequests(newToken)
    }

    function logout() {
        token.value = null
        user.value = null
        allProjects.value = []
        localStorage.removeItem('jwtToken')
        localStorage.removeItem('user')
        localStorage.removeItem('allProjects')
    }

    async function fetchProjects(): Promise<void> {
        const apiBaseUrl = useApiBaseUrl()
        try {
            const response = await fetchWithAuth(`${apiBaseUrl}/api/v1/settings/projects`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token.value}`,
                },
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Error fetching projects')
            }

            const data: string[] = await response.json()
            allProjects.value = data
            logger.debug('Fetched projects:', allProjects.value)
            localStorage.setItem('allProjects', JSON.stringify(data))
        } catch (error) {
            logger.error('Fetch projects failed:', error)
            allProjects.value = []
        }
    }

    function decodeToken(): void {
        user.value = token.value ? jwtDecode<User>(token.value) : null
    }

    return {
        token,
        user,
        allProjects,
        showLoginModal,
        isAuthenticated,
        isSuperAdmin,
        getUserProjects,
        filteredProjects,
        isAdminForProject,
        login,
        logout,
        fetchProjects,
        decodeToken,
    }
})
