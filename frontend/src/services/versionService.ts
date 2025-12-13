import { useApi } from '@/composables/useApi'
import { useApiBaseUrl } from '@/composables/useApiBaseUrl'
import type {components} from "@/api/openapi";

type ticketProject = components["schemas"]["TicketProject"];

const { fetchWithAuth } = useApi()
const apiBaseUrl = useApiBaseUrl()

export async function createVersion(projectName: string, versionName: string): Promise<any> {
    const baseUrl = `${apiBaseUrl}/api/v1/projects/${projectName}/versions`
    const postResp = await fetchWithAuth(baseUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version: versionName }),
    })

    if (!postResp.ok) {
        const text = await postResp.text().catch(() => '')
        throw new Error(`Failed to create version: ${postResp.status} ${text}`)
    }

    return await postResp.json()
}

export async function getVersion(projectName: string, versionName: string):Promise<any>{
    const baseUrl = `${apiBaseUrl}/api/v1/projects/${projectName}/versions/${versionName}`
    const detailsResp = await fetchWithAuth(`${baseUrl}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    })

    if (!detailsResp.ok) {
        const text = await detailsResp.text().catch(() => '')
        throw new Error(`Failed to fetch version details: ${detailsResp.status} ${text}`)
    }

    return await detailsResp.json()
}

export async function getVersions(projectName: string, sections: string):Promise<ticketProject>{
    const response = await fetchWithAuth(
        `${apiBaseUrl}/api/v1/projects/${projectName}?sections=${sections}`
    );
    if (!response.ok) {
        throw new Error((await response.json()).detail);
    }
    return  await response.json();
}