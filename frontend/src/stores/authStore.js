// src/stores/authStore.js
import {defineStore} from "pinia";
import {jwtDecode} from "jwt-decode";
import {useApiBaseUrl} from "../composables/useApiBaseUrl.js";
import {ref, computed} from "vue";
import {useApi} from "../composables/useApi.js";

export const useAuthStore = defineStore("auth", () => {
    // State
    const token = ref(null);
    const user = ref(JSON.parse(localStorage.getItem("user")) || null);
    const allProjects = ref(JSON.parse(localStorage.getItem("allProjects")) || []);
    const showLoginModal = ref(false);
    const {retryRequests, fetchWithAuth} = useApi();

    // Getters
    const isAuthenticated = computed(() => !!token.value);
    const isSuperAdmin = computed(() => user.value?.scopes?.["*"] === "admin");
    const getUserProjects = computed(() =>
        Object.keys(user.value?.scopes || {}).filter((p) => p !== "*")
    );
    const isAdminForProject = (project) => user.value?.scopes?.[project] === "admin";

    const filteredProjects = computed(() =>
        isSuperAdmin.value ? allProjects.value : getUserProjects.value
    );

    // Actions
    function login(newToken) {
        token.value = newToken;
        localStorage.setItem("jwtToken", newToken);
        user.value = jwtDecode(newToken);
        localStorage.setItem("user", JSON.stringify(user.value));
        showLoginModal.value = false;
        retryRequests(newToken);
    }

    function logout() {
        token.value = null;
        user.value = null;
        allProjects.value = [];
        localStorage.removeItem("jwtToken");
        localStorage.removeItem("user");
        localStorage.removeItem("allProjects");
    }

    async function fetchProjects() {
        const apiBaseUrl = useApiBaseUrl();
        try {
            const response = await fetchWithAuth(`${apiBaseUrl}/api/v1/settings/projects`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token.value}`,
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Error fetching projects");
            }

            const data = await response.json();
            allProjects.value = data;
            console.log("Fetched projects:", allProjects.value);
            localStorage.setItem("allProjects", JSON.stringify(data));
        } catch (error) {
            console.error("Fetch projects failed:", error);
            allProjects.value = [];
        }
    }


    function decodeToken() {
        user.value = token.value ? jwtDecode(token.value) : null;
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
    };
});

