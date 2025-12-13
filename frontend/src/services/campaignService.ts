import {useApi} from '@/composables/useApi';
import {useApiBaseUrl} from '@/composables/useApiBaseUrl';
import {logger} from '@/composables/logger';
import type {components} from "@/api/openapi";

type TicketProject = components['schemas']['TicketProject'];
type CampaignLights = components['schemas']['CampaignLights'];
type CampaignLight = components['schemas']['CampaignLight'];
type CampaignProjections = components['schemas']['CampaignProjections'];
type CampaignFull = components['schemas']['CampaignFull'];
type CampaignPatch = components['schemas']['CampaignPatch'];

export async function getProjectDetails(projectName: string, sections: string = 'current,future'): Promise<{
    data: TicketProject
}> {
    const params = new URLSearchParams({
        sections: sections
    });

    try {
        const {fetchWithAuth} = useApi();
        const response = await fetchWithAuth(`${useApiBaseUrl()}/api/v1/projects/${projectName}?${params}`);

        const data = await response.json();
        return {data};
    } catch (error) {
        logger.error('Failed to fetch project versions:', error);
        throw error;
    }
}

export async function getVersionOccurrences(projectName: string,
                                            version: string,
                                            offSet: number = 0,
                                            limit: number = 10,
): Promise<{ data: CampaignLights, total: number }> {
    const params = new URLSearchParams({
        skip: offSet.toString(),
        limit: limit.toString(),
        version: version,
    });

    try {
        const {fetchWithAuth} = useApi();
        const response = await fetchWithAuth(`${useApiBaseUrl()}/api/v2/projects/${projectName}/campaigns?${params}`);

        const totalHeader = response.headers.get('X-Total-Count');
        const total = totalHeader ? parseInt(totalHeader, 10) : 0;

        const data = await response.json();
        return {data, total};

    } catch (error) {
        logger.error('Failed to fetch project campaigns:', error);
        throw error;
    }
}

export async function getCampaignProjections(projectName: string,
                                             projection: string = 'campaigns',
                                             limit: number = 10,
                                             skip: number = 0): Promise<CampaignProjections> {
    const params = new URLSearchParams({
        skip: skip.toString(),
        limit: limit.toString(),
        projection: projection,
    });
    console.log("in get campaign Projections");
    try {
        const {fetchWithAuth} = useApi();
        const response = await fetchWithAuth(`${useApiBaseUrl()}/api/v2/projects/${projectName}?${params}`);

        return await response.json();

    } catch (error) {
        logger.error('Failed to fetch project campaigns:', error);
        throw error;
    }
}


export async function getCampaignVersionOccurrence(projectName:string, version:string, occurrence:number): Promise<CampaignFull> {
    try {
        const {fetchWithAuth} = useApi();
        const response = await fetchWithAuth(`${useApiBaseUrl()}/api/v1/projects/${projectName}/campaigns/${version}/${occurrence}`);

        return await response.json();
    } catch (error) {
        logger.error('Failed to fetch project campaigns version occurrence:', error);
        throw error;
    }
}

export async function createCampaign(projectName: string, version: string): Promise<CampaignLight> {
    try {
        const {fetchWithAuth} = useApi();
        const response = await fetchWithAuth(`${useApiBaseUrl()}/api/v1/projects/${projectName}/campaigns`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({version: version})
            });

        return await response.json();
    } catch (error) {
        logger.error('Failed to fetch project campaigns version occurrence:', error);
        throw error;
    }
}

export async function campaignNextStatuses(projectName: string, currentStatus: string): Promise<any>{
    try{
        logger.debug(`project: ${projectName}, current status ${currentStatus}`);
        const {fetchWithAuth} = useApi();
        const response = await fetchWithAuth(
            `${useApiBaseUrl()}/api/v1/settings/projects/${projectName}/campaigns/${currentStatus}`);
        return await response.json();
    } catch (error) {
        logger.error('Failed to fetch project campaigns next statuses:', error);
        throw error;
    }
}

export async function updateCampaignDescriptionStatus(projectName: string,
                                                      version: string,
                                                      occurrence: number,
                                                      payload: CampaignPatch):Promise<CampaignLight>{
    try{
        logger.debug(`Project name ${projectName}, version ${version}, occurrence ${occurrence}, payload ${payload}`);
        const {fetchWithAuth} = useApi();
        const response = await fetchWithAuth(
            `${useApiBaseUrl()}/api/v1/projects/${projectName}/campaigns/${version}/${occurrence}`,
            {
                method: 'PATCH',
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload)
            });
        return await response.json();
    }catch (error) {
        logger.error('Failed to patch project campaigns:', error);
        throw error;
    }
}