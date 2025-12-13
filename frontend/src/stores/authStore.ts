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
    const apiBaseUrl = useApiBaseUrl()
    // State
    const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))
    const allProjects = ref<string[]>(JSON.parse(localStorage.getItem('allProjects') || '[]'))
    const showLoginModal = ref(false)

    const { retryRequests, fetchWithAuth } = useApi()
    // Helpers

    // Getters
    const isAuthenticated = computed(() => !!user.value)

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
    async function login(formBody: string): Promise<void> {
        const response = await fetch(`${apiBaseUrl}/api/v1/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: formBody
        })
        if (!response.ok) {
          const err = await response.json()
          throw new Error(err.detail || 'Error logging in')
        }
        const data = await response.json()
        const token = data.access_token
        user.value = jwtDecode<User>(token)
        await fetchProjects();
        localStorage.setItem('user', JSON.stringify(user.value))
        showLoginModal.value = false
        await retryRequests(token)
    }

    function logout() {
        user.value = null
        allProjects.value = []
        localStorage.setItem('user', 'null')
        localStorage.setItem('allProjects', '[]')
    }

    async function fetchProjects(): Promise<void> {
        const apiBaseUrl = useApiBaseUrl()
        try {
            const response = await fetchWithAuth(`${apiBaseUrl}/api/v1/settings/projects`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Error fetching projects')
            }

            const data: string[] = await response.json()
            logger.debug(data);
            allProjects.value = data
            logger.debug('Fetched projects:', allProjects.value)
            localStorage.setItem('allProjects', JSON.stringify(data))
        } catch (error) {
            logger.error('Fetch projects failed:', error)
            allProjects.value = []
        }
    }


    return {
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
    }
})
