import {defineStore} from 'pinia'
import {ref, computed} from 'vue'
import type {components} from "@/api/openapi";
import {
    getCampaignProjections,
    createCampaign,
    getCampaignVersionOccurrence,
    updateCampaignDescriptionStatus
} from "@/services/campaignService";
import {logger} from "@/composables/logger";

type CampaignProjections = components["schemas"]["CampaignProjections"];
type CampaignFull = components["schemas"]["CampaignFull"];
type Status = CampaignFull['status'];
type CampaignLight = components['schemas']['CampaignLight'];

export const useCampaignStore = defineStore('campaignStore', () => {
    // states
    const projectName = ref<string | null>(null);
    const version = ref<string | null>(null);
    const occurrence = ref<number | null>(null);
    const versionCampaigns = ref<CampaignProjections | null>(null);
    const isLoading = ref<boolean>(false);
    const limit = ref(10);
    const skip = ref(0);
    const currentCampaign = ref<CampaignFull | null>(null);

    // getters
    const versions = computed(() => {
        if (versionCampaigns.value === null) return []
        return versionCampaigns.value.data.map(({version, status}) => ({
            version,
            status,
        }))
    })

    const versionOccurrences = computed(() => {
        return (expectedVersion: string) => {
            const cp = versionCampaigns.value?.data.find(v => v.version === expectedVersion);
            return cp?.occurrences || []
        }
    })

    const currentLimit = computed(() => limit.value);
    const currentSkip = computed(() => skip.value);
    const hasMore = () => versionCampaigns.value === null || skip.value < versionCampaigns.value.count;

    // actions
    async function getVersionCampaigns(reset: boolean = false) {
        logger.debug("in getVersionCampaigns")
        if (!projectName.value) {
            return
        }
        if (reset) {
            skip.value = 0;
            versionCampaigns.value = null;
        }
        isLoading.value = true;
        try {
            logger.debug("Before getCampaignProjections call")
            const tempVersionCampaign: CampaignProjections = await getCampaignProjections(
                projectName.value,
                'campaigns',
                limit.value,
                skip.value);
            logger.debug('Received from service\n' + JSON.stringify(tempVersionCampaign));
            if (reset || !versionCampaigns.value) {
                versionCampaigns.value = tempVersionCampaign;
            } else {
                versionCampaigns.value.data.push(...tempVersionCampaign.data)
            }
            skip.value += tempVersionCampaign.data.length
        } catch (e: any) {
            logger.error(e);
            throw e;
        } finally {
            isLoading.value = false;
        }
    }

    function selectOccurrence(occurrenceSelected: number) {
        occurrence.value = occurrenceSelected;
    }

    function selectVersion(versionSelected: string) {
        occurrence.value = null;
        version.value = versionSelected;
    }

    async function createNewOccurrence(versionSelected: string) {
        if (!projectName.value)
            return
        const newOccurrence: CampaignLight = await createCampaign(projectName.value, versionSelected);
        const target = versionCampaigns.value?.data.find(v => v.version === versionSelected);
        if (target) {
            target.occurrences.push({occurrence: newOccurrence.occurrence, status: newOccurrence.status})
        }

    }

    async function retrieveCampaignOccurrence(projectName: string,
                                              version: string,
                                              occurrence: number) {

        currentCampaign.value = await getCampaignVersionOccurrence(projectName,
            version,
            occurrence)
    }

    async function updateCampaignOccurrenceStatus(selectedStatus: string) {
        if (!currentCampaign.value) {
            throw new Error("No campaign selected");
        }
        const allowed: Status[] = ["in progress", "recorded", "done", "cancelled", "closed", "paused"];
        if (!allowed.includes(selectedStatus as Status)) {
            throw new Error("Invalid status");
        }

        currentCampaign.value.status = selectedStatus as Status;
        logger.debug("Call to campaignService");
        try {
            const response: CampaignLight = await updateCampaignDescriptionStatus(
                currentCampaign.value.project_name,
                currentCampaign.value.version,
                currentCampaign.value.occurrence,
                {status: currentCampaign.value.status});
            if (response.status != selectedStatus) {
                throw new Error("Could not update status");
            }
        } catch (e: any) {
            logger.error(e);
            throw e;
        }
    }

    async function updateCampaignOccurrenceDescription(newDescription: string) {
        if (!currentCampaign.value) {
            throw new Error("No campaign selected");
        }
        currentCampaign.value.description = newDescription;
        logger.debug("Call to campaignService");
        try {
            const response = await updateCampaignDescriptionStatus(
                currentCampaign.value.project_name,
                currentCampaign.value.version,
                currentCampaign.value.occurrence,
                {description: newDescription});
            if (response.description != newDescription) {
                throw new Error("Could not update description");
            }
        } catch (e: any) {
            logger.error(e);
            throw e;
        }
    }

    return {
        projectName,
        version,
        occurrence,
        versionCampaigns,
        versions,
        versionOccurrences,
        currentCampaign,
        isLoading,
        currentSkip,
        currentLimit,
        hasMore,
        selectVersion,
        selectOccurrence,
        getVersionCampaigns,
        createNewOccurrence,
        retrieveCampaignOccurrence,
        updateCampaignOccurrenceDescription,
        updateCampaignOccurrenceStatus
    }
})