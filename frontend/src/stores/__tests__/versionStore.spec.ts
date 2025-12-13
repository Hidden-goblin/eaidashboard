import {describe, it, expect, beforeEach, afterEach, vi} from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { getVersions } from "@/services/versionService";
import type {Mock} from 'vitest';
import {useVersionStore} from "@/stores/versionStore";
vi.mock("@/services/versionService", () => ({
    createVersion: vi.fn(),
    getVersion: vi.fn(),
    getVersions: vi.fn()
}))

const mockedGetVersions = getVersions as unknown as Mock;

describe('versionStore (with mocked versionService)', () => {
    beforeEach(async () => {
        setActivePinia(createPinia());
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.clearAllMocks();
        vi.restoreAllMocks();
    });

    it('fetchVersions populates the selectedType slot from service', async () => {
        // arrange: selected project + mock response for "current"
        const store = useVersionStore();
        store.selectedProject = 'projA';
        store.selectedType = 'current';
        mockedGetVersions.mockResolvedValueOnce({
            name: 'projA',
            current: [{version: 'v1', created: 'c', updated: 'u', started: null, end_forecast: null, status: 'open'}],
            future: [],
            archived: [],
        });

        // act
        await store.fetchVersions();

        // assert
        expect(mockedGetVersions).toHaveBeenCalledWith('projA', 'current');
        expect(store.versions.current).toHaveLength(1);
        expect(store.displayedVersions).toEqual(store.versions.current);
    });

    it('displayedVersions follows selectedType', async () => {
        // arrange: seed versions directly
        const store = useVersionStore();
        store.versions = {
            name: 'p',
            current: [{version: 'c'} as any],
            future: [{version: 'f1'} as any, {version: 'f2'} as any],
            archived: [],
        };

        // act/assert for current
        store.selectedType = 'current';
        expect(store.displayedVersions).toEqual(store.versions.current);

        // act/assert for future
        store.selectedType = 'future';
        expect(store.displayedVersions).toEqual(store.versions.future);
    });

    it('addVersion fetches future when empty and appends the new version', async () => {
        // arrange
        const store = useVersionStore();
        store.selectedProject = 'projA';
        // make future empty initially
        store.versions = {name: 'projA', current: [], future: [], archived: []};

        // mock getVersions for "future" returning one existing future version
        mockedGetVersions.mockResolvedValueOnce({
            name: 'projA',
            current: [],
            future: [{
                version: 'f-existing',
                created: '',
                updated: '',
                started: null,
                end_forecast: null,
                status: 'open'
            }],
            archived: [],
        });

        const newVersion = {
            version: 'f-new',
            created: '',
            updated: '',
            started: null,
            end_forecast: null,
            status: 'open'
        };

        // act
        await store.addVersion(newVersion);

        // assert: service was called to populate future, and newVersion appended
        expect(mockedGetVersions).toHaveBeenCalledWith('projA', 'future');
        expect((store.versions.future ?? []).map((v: any) => v.version)).toContain('f-existing');
        expect((store.versions.future ?? []).map((v: any) => v.version)).toContain('f-new');
    });

    it('addVersion appends without calling service when future already populated', async () => {
        // arrange: future already has a value
        const store = useVersionStore();
        store.versions = {
            name: 'projA',
            current: [],
            future: [{version: 'f1'} as any],
            archived: [],
        };
        const newVersion = {version: 'f2', created: '', updated: '', started: null, end_forecast: null, status: 'open'};

        // act
        await store.addVersion(newVersion);

        // assert
        expect(mockedGetVersions).not.toHaveBeenCalled();
        expect((store.versions.future ?? []).map((v: any) => v.version)).toEqual(['f1', 'f2']);
    });

    it('resetVersions restores the initial empty shape', () => {
        // arrange: mutate store
        const store = useVersionStore();
        store.versions = {
            name: 'X',
            current: [{version: 'a', created: '', updated: '', started: null, end_forecast: null, status: 'open'}],
            future: [{version: 'b', created: '', updated: '', started: null, end_forecast: null, status: 'open'}],
            archived: [{version: 'c', created: '', updated: '', started: null, end_forecast: null, status: 'open'}]};

        // act
        store.resetVersions();

        // assert: reset to defaults
        expect(store.versions).toEqual({name: '', current: [], future: [], archived: []});
    });
});
