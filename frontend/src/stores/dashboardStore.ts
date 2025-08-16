import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getDashboard } from '@/services/dashboardService';
import { logger } from "@/composables/logger";
import type { components } from "@/api/openapi";

type Project = components.schemas.DashboardProject;

export const useDashboardStore = defineStore('dashboard', () => {
  const projects = ref<Project[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const offset = ref(0);
  const limit = 10; // page size
  const totalCount = ref<number | null>(null); // total from header

  async function fetchDashboardData(reset = false) {
    if (reset) {
      offset.value = 0;
      projects.value = [];
      totalCount.value = null;
    }

    isLoading.value = true;
    error.value = null;

    try {
      const { data, total } = await getDashboard(offset.value, limit);
      projects.value.push(...data.projects);
      totalCount.value = total;
      offset.value += limit;
    } catch (e: any) {
      error.value = e?.message || 'Failed to fetch dashboard data.';
      logger.error(e);
    } finally {
      isLoading.value = false;
    }
  }

  const hasMore = () => totalCount.value === null || offset.value < totalCount.value;

  return {
    projects,
    isLoading,
    error,
    fetchDashboardData,
    hasMore,
  };
});
