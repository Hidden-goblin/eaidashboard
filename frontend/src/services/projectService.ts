import {useApi} from "@/composables/useApi";
import {useApiBaseUrl} from "@/composables/useApiBaseUrl";

const { fetchWithAuth } = useApi()
const apiBaseUrl = useApiBaseUrl()

export async function createProject(projectName: string): Promise<any> {
    const baseUrl = `${apiBaseUrl}/api/v1/settings/projects`
    const postResp = await fetchWithAuth(baseUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: projectName }),
    })

    if (!postResp.ok) {
        const text = await postResp.text().catch(() => '')
        throw new Error(`Failed to create project: ${postResp.status} ${text}`)
    }

    return await postResp.json()
}