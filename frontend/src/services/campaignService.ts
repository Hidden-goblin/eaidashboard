import {useApi} from '@/composables/useApi';
import {useApiBaseUrl} from '@/composables/useApiBaseUrl';
import {logger} from '@/composables/logger';
import type {components} from "@/api/openapi";

type TicketProject = components.schemas.TicketProject;
type CampaignLights = components.schemas.CampaignLights;

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
                                            ): Promise<{ data: CampaignLights, total: number}>{
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
        return { data, total };

    } catch (error) {
        logger.error('Failed to fetch project campaigns:', error);
        throw error;
    }
}