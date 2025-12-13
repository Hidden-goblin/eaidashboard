import { useApi } from '@/composables/useApi';
import { useApiBaseUrl } from '@/composables/useApiBaseUrl';
import { logger } from '@/composables/logger';
import type { components } from "@/api/openapi";

type Dashboard = components["schemas"]["Dashboard"];

export async function getDashboard(offSet = 0, limit = 10): Promise<{ data: Dashboard, total: number }> {
    const params = new URLSearchParams({
        skip: offSet.toString(),
        limit: limit.toString(),
    });

    try {
        const { fetchWithAuth } = useApi();
        const response = await fetchWithAuth(`${useApiBaseUrl()}/api/v2/dashboard?${params}`);

        const totalHeader = response.headers.get('X-Total-Count');
        const total = totalHeader ? parseInt(totalHeader, 10) : 0;

        const data = await response.json();
        return { data, total };
    } catch (error) {
        logger.error('Failed to fetch dashboard:', error);
        throw error;
    }
}
