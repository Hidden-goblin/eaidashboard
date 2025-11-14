import {defineStore} from 'pinia'
import {ref, computed} from 'vue'
import type {components} from "@/api/openapi";
import {getCampaignProjections, createCampaign, getCampaignVersionOccurrence, updateCampaignDescriptionStatus} from "@/services/campaignService";
import {logger} from "@/composables/logger";

type CampaignProjections = components.schemas.CampaignProjections;
type CampaignFull = components.schemas.CampaignFull;

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
            const cp = versionCampaigns.value.data.find(v => v.version === expectedVersion);
            return cp.occurrences
        }
    })

    const hasMore = () => versionCampaigns.value === null || skip.value < versionCampaigns.value.count;

    // actions
    async function getVersionCampaigns(reset: boolean = false) {
        logger.debug("in getVersionCampaigns")
        if (reset) {
            skip.value = 0;
            versionCampaigns.value = null;
        }
        isLoading.value = true;
        try {
            const tempVersionCampaign: CampaignProjections = await getCampaignProjections(
                projectName.value,
                'campaigns',
                limit.value,
                skip.value);
            if (reset) {
                versionCampaigns.value = tempVersionCampaign;
            } else {
                versionCampaigns.value.data.push(...tempVersionCampaign.data)
            }
            skip.value += limit.value;
        } catch (e: any) {
            logger.error(e);
            throw e;
        } finally {
            isLoading.value = false;
        }
    }

    function selectOccurrence(occurrenceSelected: int) {
        occurrence.value = occurrenceSelected;
    }

    function selectVersion(versionSelected: string) {
        occurrence.value = null;
        version.value = versionSelected;
    }

    async function createNewOccurrence(versionSelected: string) {
        const newOccurrence = await createCampaign(projectName.value, versionSelected);
        const target = versionCampaigns.value.data.find(v => v.version === versionSelected);
        if (target) {
            target.occurrences.push({occurrence: newOccurrence.occurrence, status: newOccurrence.status})
        }

    }

    async function retrieveCampaignOccurrence(projectName: string,
                                              version: string,
                                              occurrence: int) {

        currentCampaign.value = await getCampaignVersionOccurrence(projectName,
            version,
            occurrence)
    }

    async function updateCampaignOccurrenceStatus(selectedStatus: string){
        currentCampaign.value.status = selectedStatus;
        logger.debug("Call to campaignService");
        try{
            const response = await updateCampaignDescriptionStatus(
                currentCampaign.value.project_name,
                currentCampaign.value.version,
                currentCampaign.value.occurrence,
                {status: selectedStatus});
            if (response.status != selectedStatus || response.detail){
                throw new Error("Could not update description");
            }
        }catch (e: Any){
            logger.error(e);
            throw e;
        }
    }

    async function updateCampaignOccurrenceDescription(newDescription: string){
        currentCampaign.value.description = newDescription;
        logger.debug("Call to campaignService");
        try{
            const response = await updateCampaignDescriptionStatus(
                currentCampaign.value.project_name,
                currentCampaign.value.version,
                currentCampaign.value.occurrence,
                {description: newDescription});
            if (response.description != newDescription){
                throw new Error("Could not update description");
            }
        }catch (e: Any){
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