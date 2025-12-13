import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import * as dashboardService from '@/services/dashboardService';
import { useDashboardStore } from '@/stores/dashboardStore';

describe('dashboardStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia());
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('fetchDashboardData with reset=true replaces projects, sets total and stops loading', async () => {
        const fakeProjects = [{ alias: 1, name: 'p1' }];
        vi.spyOn(dashboardService, 'getDashboard').mockResolvedValue({
            data: { projects: fakeProjects },
            total: 2,
        } as any);

        const store = useDashboardStore();
        await store.fetchDashboardData(true);

        expect(store.projects.length).toBe(1);
        expect(store.projects[0]).toEqual(fakeProjects[0]);
        expect(store.error).toBeNull();
        expect(store.isLoading).toBe(false);
        // after one fetch offset becomes 10 (limit) so hasMore should be false when total=2
        expect(store.hasMore()).toBe(false);
    });

    it('fetchDashboardData with reset=false appends projects and updates hasMore', async () => {
        const page1 = [{ alias: 1 }];
        const page2 = [{ alias: 2 }, { alias: 3 }];
        const spy = vi.spyOn(dashboardService, 'getDashboard');
        spy.mockResolvedValueOnce({ data: { projects: page1 }, total: 30 } as any);
        spy.mockResolvedValueOnce({ data: { projects: page2 }, total: 30 } as any);

        const store = useDashboardStore();
        await store.fetchDashboardData(true); // load first page
        expect(store.projects.length).toBe(1);
        expect(store.hasMore()).toBe(true); // offset (10) < total (30)

        await store.fetchDashboardData(false); // load second page
        expect(store.projects.length).toBe(3);
        expect(store.projects.map(p => p.alias)).toEqual([1, 2, 3]);
        // after two fetches offset == 20, still less than 30
        expect(store.hasMore()).toBe(true);
    });

    it('fetchDashboardData sets error when service throws', async () => {
        vi.spyOn(dashboardService, 'getDashboard').mockRejectedValue(new Error('boom'));

        const store = useDashboardStore();
        await store.fetchDashboardData(true);

        expect(store.error).toBe('boom');
        expect(store.isLoading).toBe(false);
    });

    it('hasMore returns true when totalCount is null (no request done yet)', () => {
        const store = useDashboardStore();
        // before any fetch totalCount is null
        expect(store.hasMore()).toBe(true);
    });
});
