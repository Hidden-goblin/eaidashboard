// /components/__tests__/CreateVersionForm.spec.ts
import { render, fireEvent, screen, waitFor } from '@testing-library/vue'
import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import CreateVersionForm from '@/components/versions/CreateVersionForm.vue'
import { server } from '@/mocks/node'
import { logger } from "@/composables/logger";
import { versionHandler } from "@/mocks/versionHandler";


vi.mock('@/composables/useApiBaseUrl', () => ({
    useApiBaseUrl: () => 'http://mock-api'
}))



beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('CreateVersionForm.vue', () => {
    it('Render the form with version input, create and cancel button', async () => {
        render(CreateVersionForm, {
            global: {
                plugins: [createTestingPinia()]
            },
            props: {
                projectName: 'demo'
            }
        })

        expect(screen.getByTestId('versionNameInput')).toBeTruthy();
        expect(screen.getByTestId('createVersionButton')).toBeTruthy();
        expect(screen.getByTestId('cancelCreateVersionButton')).toBeTruthy();
    })

    it('Cancel emits a close event', async () => {
        const {emitted} = render(CreateVersionForm, {
            global: {
                plugins: [createTestingPinia()]
            },
            props: {
                projectName: 'demo'
            }
        });

        await fireEvent.click(screen.getByTestId('cancelCreateVersionButton'))
        expect(emitted()['close']).toBeTruthy()
    })

    it('Create a new version in success', async () => {
        const {emitted} = render(CreateVersionForm, {
            props: {projectName: 'demo'},
        });
        server.use( ...versionHandler )
        await fireEvent.update(screen.getByTestId('versionNameInput'), "1.1");
        await fireEvent.click(screen.getByTestId('createVersionButton'));
        await waitFor(() => {
            logger.debug(emitted())
            expect(emitted()['version-created']).toBeTruthy();
        })
    })

    // it('User is not authenticated')

    // it('Show spinner if request is delayed', async () => {
    //     //TODO: move this test to loadingStore testing
    //     const pinia = createPinia();
    //     setActivePinia(pinia);
    //     server.use(
    //         http.post('http://mock-api/api/v1/projects/demo/versions', async ({request}) => {
    //                 logger.debug("Override post create")
    //                 await delay(200);
    //                 logger.debug('after delay')
    //                 return HttpResponse.json({inserted_id: '12', acknowledged: true, message: ''}, {status: 200});
    //             }
    //         ))
    //     render(CreateVersionForm, {
    //         global: { plugins: [pinia]},
    //         props: {projectName: 'demo'},
    //     });
    //     const loadingStore = useLoadingStore(pinia);
    //     const { isLoading } = storeToRefs(loadingStore);
    //     await fireEvent.update(screen.getByTestId('versionNameInput'), "1.1");
    //     await fireEvent.click(screen.getByTestId('createVersionButton'));
    //     await waitFor(() => {
    //         logger.debug("Waiting for spinner")
    //         expect(isLoading.value).toBe(true);
    //     })
    //
    //     // spinner should eventually disappear
    //     await waitFor(() => {
    //         expect(isLoading.value).toBe(false);
    //     })
    // });
})
