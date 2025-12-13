import { describe, it, beforeEach, vi, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import CampaignDetails from '@/components/campaigns/CampaignDetails.vue'

let mockStore: any

// Mock pinia's storeToRefs to forward the refs from our mock store
vi.mock('pinia', () => ({
    storeToRefs: (s: any) => ({
        projectName: s.projectName,
        version: s.version,
        occurrence: s.occurrence,
        currentCampaign: s.currentCampaign
    })
}))

// Mock the campaign store module to return the current mockStore variable
vi.mock('@/stores/campaignStore', () => ({
    useCampaignStore: () => mockStore
}))

function pause() {
    return new Promise((r) => setTimeout(r, 0))
}

describe('CampaignDetails', () => {
    beforeEach(() => {
        // recreate refs and default mock implementation per test
        mockStore = {
            projectName: ref('proj-a'),
            version: ref(''),
            occurrence: ref<null | number>(null),
            currentCampaign: ref(null),
            retrieveCampaignOccurrence: vi.fn(async () => {})
        }
        vi.clearAllMocks()
    })

    it('renders default message when no version or occurrence selected', async () => {
        mockStore.version.value = ''
        mockStore.occurrence.value = null
        const wrapper = shallowMount(CampaignDetails, {
            global: {
                // stub child to avoid rendering real implementation
                stubs: {
                    VersionCampaignOccurrenceDetails: {
                        template: '<div data-test="child">child</div>'
                    }
                }
            }
        })

        // watch is immediate; wait a tick for updates
        await nextTick()
        expect(wrapper.text()).toContain('Select a version and occurrence to view details.')
        expect(mockStore.retrieveCampaignOccurrence).not.toHaveBeenCalled()
    })

    it('shows loading while retrieving and then renders child after success', async () => {
        // setup controlled deferred promise so we can assert loading state
        let resolveRetrieval: () => void
        const retrievalPromise = new Promise<void>((res) => {
            resolveRetrieval = res
        })

        mockStore.version.value = 'v1'
        mockStore.occurrence.value = 1
        mockStore.currentCampaign.value = null
        mockStore.retrieveCampaignOccurrence = vi.fn(async () => {
            // wait until test resolves
            await retrievalPromise
            // simulate store updating currentCampaign after retrieval
            mockStore.currentCampaign.value = { id: 'c1' }
        })

        const wrapper = shallowMount(CampaignDetails, {
            global: {
                stubs: {
                    VersionCampaignOccurrenceDetails: {
                        template: '<div data-test="child">child</div>'
                    }
                }
            }
        })

        // Immediately after mount the watcher sets loading=true -> loading UI appears
        await nextTick()
        expect(wrapper.text()).toContain('Loading campaign details...')

        // finish retrieval
        resolveRetrieval!()
        // wait for promise resolution and component updates
        await pause()
        await nextTick()

        // now child should be rendered
        expect(wrapper.find('[data-test="child"]').exists()).toBe(true)
        expect(mockStore.retrieveCampaignOccurrence).toHaveBeenCalledWith('proj-a', 'v1', 1)
    })

    it('displays an error message when retrieveCampaignOccurrence throws', async () => {
        mockStore.version.value = 'v2'
        mockStore.occurrence.value = 2
        mockStore.retrieveCampaignOccurrence = vi.fn(async () => {
            throw new Error('boom')
        })

        const wrapper = shallowMount(CampaignDetails, {
            global: {
                stubs: {
                    VersionCampaignOccurrenceDetails: {
                        template: '<div data-test="child">child</div>'
                    }
                }
            }
        })

        // wait for watcher to run and handle the rejection
        await pause()
        await nextTick()

        expect(wrapper.text()).toContain('⚠️')
        expect(wrapper.text()).toContain('boom')
        expect(mockStore.retrieveCampaignOccurrence).toHaveBeenCalled()
    })

    it('renders child when currentCampaign is already present after retrieval completes', async () => {
        // simulate retrieve as fast resolved and currentCampaign present
        mockStore.version.value = 'v3'
        mockStore.occurrence.value = 3
        mockStore.currentCampaign.value = { id: 'existing' }
        mockStore.retrieveCampaignOccurrence = vi.fn(async () => {
            // no change, resolved immediately
        })

        const wrapper = shallowMount(CampaignDetails, {
            global: {
                stubs: {
                    VersionCampaignOccurrenceDetails: {
                        template: '<div data-test="child">child</div>'
                    }
                }
            }
        })

        // wait for any microtasks
        await pause()
        await nextTick()

        expect(wrapper.find('[data-test="child"]').exists()).toBe(true)
        expect(mockStore.retrieveCampaignOccurrence).toHaveBeenCalledWith('proj-a', 'v3', 3)
    })
})
