import {describe, it, expect, beforeEach, vi} from 'vitest';
import {setActivePinia, createPinia} from 'pinia';
import {useCampaignStore} from '@/stores/campaignStore';
import {
    getCampaignProjections,
    createCampaign,
    getCampaignVersionOccurrence,
    updateCampaignDescriptionStatus
} from '@/services/campaignService';
import type {Mock} from 'vitest';

// Mock the service and logger modules
vi.mock('@/services/campaignService', () => ({
    getCampaignProjections: vi.fn(),
    createCampaign: vi.fn(),
    getCampaignVersionOccurrence: vi.fn(),
    updateCampaignDescriptionStatus: vi.fn()
}));

// Helpers to satisfy TS about mocks
const mockedGetCampaignProjections = getCampaignProjections as unknown as Mock;
const mockedCreateCampaign = createCampaign as unknown as Mock;
const mockedGetCampaignVersionOccurrence = getCampaignVersionOccurrence as unknown as Mock;
const mockedUpdateCampaignDescriptionStatus = updateCampaignDescriptionStatus as unknown as Mock;

describe('campaignStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia());
        vi.clearAllMocks();
    });

    it('loads version campaigns (reset) and advances skip', async () => {
        const store = useCampaignStore();
        store.projectName = 'testProject';
        const sample: any = {
            count: 2,
            data: [
                {version: 'v1', status: 'done', occurrences: [{occurrence: 1, status: 'done'}]},
                {version: 'v2', status: 'in progress', occurrences: []}
            ]
        };
        mockedGetCampaignProjections.mockResolvedValueOnce(sample);

        await store.getVersionCampaigns(true);
        expect(mockedGetCampaignProjections).toHaveBeenCalled();

        expect(store.versionCampaigns).toEqual(sample);
        expect(store.currentSkip).toBe(2);
    });

    it('appends additional pages when not reset', async () => {
        const store = useCampaignStore();
        store.projectName = 'testProject';
        const first: any = {count: 2, data: [{version: 'v1', status: 'done', occurrences: []}]};
        const second: any = {count: 2, data: [{version: 'v2', status: 'in progress', occurrences: []}]};

        mockedGetCampaignProjections.mockResolvedValueOnce(first);
        await store.getVersionCampaigns(true);
        expect(mockedGetCampaignProjections).toHaveBeenCalled();
        expect(store.versionCampaigns).toEqual(first);
        expect(store.currentSkip).toBe(1);

        mockedGetCampaignProjections.mockResolvedValueOnce(second);
        await store.getVersionCampaigns(false);
        expect(mockedGetCampaignProjections).toHaveBeenCalled();
        expect(store.versionCampaigns).toEqual({
            count: 2, data: [
                {version: 'v1', status: 'done', occurrences: []},
                {version: 'v2', status: 'in progress', occurrences: []}]
        });
        expect(store.currentSkip).toBe(2);
    });

    it('logs and rethrows when getVersionCampaigns fails', async () => {
        const store = useCampaignStore();
        store.projectName = 'testProject';
        const err = new Error('network');
        mockedGetCampaignProjections.mockRejectedValueOnce(err);

        await expect(store.getVersionCampaigns(true)).rejects.toThrow('network');

    });

    it('createNewOccurrence returns early when no projectName', async () => {
        const store = useCampaignStore(); // projectName defaults to null
        await store.createNewOccurrence('v1');
        expect(mockedCreateCampaign).not.toHaveBeenCalled();
    });

    it('createNewOccurrence pushes new occurrence to matching version', async () => {
        const store = useCampaignStore();
        // set projectName so createCampaign runs
        store.projectName = 'projA';
        // populate versionCampaigns with a version with occurrence
        store.versionCampaigns = {
            count: 1,
            data: [{version: 'v1', status: 'done', occurrences: [{occurrence: 1, status: 'done'}]}]
        } as any;

        const newLight: any = {occurrence: 2, status: 'recorded'};
        mockedCreateCampaign.mockResolvedValueOnce(newLight);

        await store.createNewOccurrence('v1');

        const versionOccurrence = store.versionCampaigns!.data.find((v: any) => v.version === 'v1');
        expect(versionOccurrence?.occurrences.some((o: any) => o.occurrence === 2 && o.status === 'recorded')).toBe(true);
    });

    it('retrieveCampaignOccurrence sets currentCampaign', async () => {
        const store = useCampaignStore();
        const campaignFull: any = {project_name: 'p', version: 'v', occurrence: 1, status: 'done', description: 'd'};
        mockedGetCampaignVersionOccurrence.mockResolvedValueOnce(campaignFull);

        await store.retrieveCampaignOccurrence('p', 'v', 1);
        expect(store.currentCampaign).toEqual(campaignFull);
    });

    it('updateCampaignOccurrenceStatus throws on invalid status', async () => {
        const store = useCampaignStore();
        store.currentCampaign = {project_name: 'p', version: 'v', occurrence: 1, status: 'done'} as any;

        await expect(store.updateCampaignOccurrenceStatus('invalid-status')).rejects.toThrow('Invalid status');
    });

    it('updateCampaignOccurrenceStatus updates status and calls service on success', async () => {
        const store = useCampaignStore();
        store.currentCampaign = {project_name: 'p', version: 'v', occurrence: 1, status: 'recorded'} as any;

        mockedUpdateCampaignDescriptionStatus.mockResolvedValueOnce({status: 'done'} as any);

        await store.updateCampaignOccurrenceStatus('done');

        expect(store.currentCampaign!.status).toBe('done');
        expect(mockedUpdateCampaignDescriptionStatus).toHaveBeenCalledWith('p', 'v', 1, {status: 'done'});
    });

    it('updateCampaignOccurrenceStatus throws and logs when remote status mismatch', async () => {
        const store = useCampaignStore();
        store.currentCampaign = {project_name: 'p', version: 'v', occurrence: 1, status: 'recorded'} as any;

        mockedUpdateCampaignDescriptionStatus.mockResolvedValueOnce({status: 'recorded'} as any); // mismatch with requested 'done'

        await expect(store.updateCampaignOccurrenceStatus('done')).rejects.toThrow('Could not update status');
    });

    it('updateCampaignOccurrenceDescription updates local description on success', async () => {
        const store = useCampaignStore();
        store.currentCampaign = {project_name: 'p', version: 'v', occurrence: 1, description: 'old'} as any;

        mockedUpdateCampaignDescriptionStatus.mockResolvedValueOnce({description: 'new'} as any);

        await store.updateCampaignOccurrenceDescription('new');

        expect(store.currentCampaign!.description).toBe('new');
        expect(mockedUpdateCampaignDescriptionStatus).toHaveBeenCalledWith('p', 'v', 1, {description: 'new'});
    });

    it('updateCampaignOccurrenceDescription throws and logs when remote description mismatch', async () => {
        const store = useCampaignStore();
        store.currentCampaign = {project_name: 'p', version: 'v', occurrence: 1, description: 'old'} as any;

        mockedUpdateCampaignDescriptionStatus.mockResolvedValueOnce({description: 'other'} as any);

        await expect(store.updateCampaignOccurrenceDescription('new')).rejects.toThrow('Could not update description');
    });
});
