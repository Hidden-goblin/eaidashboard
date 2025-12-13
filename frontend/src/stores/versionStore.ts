import {defineStore} from "pinia";
import {ref, computed, watch} from "vue";
import {logger} from "@/composables/logger";
import {getVersions} from "@/services/versionService"
import type {components} from "@/api/openapi";

type TicketProject = components["schemas"]["TicketProject"];
type TicketVersion = components["schemas"]["TicketVersion"];
type VersionListKey = Exclude<keyof TicketProject, 'name'>;

export const useVersionStore = defineStore("version", () => {
    const selectedProject = ref("");
    const versions = ref<TicketProject>({
        name: "",
        current: [],
        future: [],
        archived: []
    });
    const loading = ref(false);
    const error = ref<string>("");
    const selectedType = ref<VersionListKey>("current");

    // Getter
    const displayedVersions = computed(() => versions.value[selectedType.value] || []);


    // Actions
    async function fetchVersions() {
        loading.value = true;
        // Don't fetch if versions are already loaded
        if ((versions.value[selectedType.value] ?? []).length > 0) {
            loading.value = false;
            return;
        }
        try {
            const data = await getVersions(selectedProject.value, selectedType.value);
            versions.value[selectedType.value] = data[selectedType.value] || [];
        } catch (err: unknown) {
            logger.error("Error fetching versions:", err);
            error.value = (err as Error).message ?? String(err);
        } finally {
            loading.value = false;
        }
    }

    watch(selectedProject, fetchVersions);
    watch(selectedType, fetchVersions);

    async function addVersion(newVersion: TicketVersion) {
        const future = versions.value.future ?? [];
        if (future.length === 0) {
            try {
                const data = await getVersions(selectedProject.value, "future")
                future.push(...(data['future'] ?? []));
            } catch (err: unknown) {
                logger.error("Error fetching versions:", err);
                error.value = (err as Error).message ?? String(err);
            }
        }
        future.push(newVersion);
        versions.value.future = future;
        logger.debug("Future versions" + versions.value.future);
    }

    function resetVersions() {
        versions.value = {name: '', current: [], future: [], archived: []};
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
