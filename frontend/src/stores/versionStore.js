import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import { useApiBaseUrl } from "../composables/useApiBaseUrl";
import {useAuthStore} from "../stores/authStore.js";
import {useApi} from "../composables/useApi.js";

export const useVersionStore = defineStore("version", () => {
  const apiBaseUrl = useApiBaseUrl();
  const authStore = useAuthStore();
  const selectedProject = ref("");
  const versions = ref({
    current: [],
    future: [],
    archived: []
  });
  const loading = ref(false);
  const error = ref("");
  const {fetchWithAuth} = useApi();

  const selectedType = ref("current");

  const displayedVersions = computed(() => versions.value[selectedType.value] || []);

  async function fetchVersions() {
    loading.value = true;
    // Don't fetch if versions are already loaded
    if (versions.value[selectedType.value].length > 0) {
      loading.value = false;
      return;
    }
    try {
      const response = await fetchWithAuth(
        `${apiBaseUrl}/api/v1/projects/${selectedProject.value}?sections=${selectedType.value}`,
        {
          headers: { Authorization: `Bearer ${authStore.token}` },
        }
      );
      if (!response.ok) {
        throw new Error((await response.json()).detail);
      }
      const data = await response.json();
      versions.value[selectedType.value] = data[selectedType.value] || [];
    } catch (err) {
      console.error("Error fetching versions:", err);
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  watch(selectedProject, fetchVersions);
  watch(selectedType, fetchVersions);

  async function addVersion(newVersion) {
    if (versions.value.future.length === 0) {
      try {
        const response = await fetchWithAuth(
          `${apiBaseUrl}/api/v1/projects/${selectedProject.value}?sections=future`,
          {
            headers: {Authorization: `Bearer ${authStore.token}`},
          }
        );
        if (!response.ok) {
          throw new Error((await response.json()).detail);
        }
        const data = await response.json();
        versions.value.future.push(...data['future']);
      } catch (err) {
        console.error("Error fetching versions:", err);
        error.value = err.message;
      }
    }
    versions.value.future.push(newVersion);
    console.log("Future versions" + versions.value.future);
  }

  function resetVersions() {
    versions.value = { current: [], future: [], archived: [] };
  }

  return {
    versions,
    loading,
    error,
    selectedProject,
    selectedType,
    displayedVersions,
    fetchVersions,
    addVersion,
    resetVersions,
  };
});
