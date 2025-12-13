/// <reference types="vitest/browser" />
import {render, screen, fireEvent, waitFor} from '@testing-library/vue'
import TicketForm from '../tickets/TicketForm.vue'
import {vi} from 'vitest'
import {beforeAll, afterAll, afterEach, describe, it, expect} from 'vitest'
import {server} from '@/mocks/node'
import {nextTick} from 'vue'
import {http, HttpResponse} from "msw";
// Setup mock server
vi.mock('@/composables/useApiBaseUrl', () => ({
    useApiBaseUrl: () => 'http://mock-api'
}))


beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('TicketForm', () => {
    it('renders the form inputs', () => {
        render(TicketForm, {
            props: {
                projectName: 'demo',
                versionId: 'v1'
            }
        })

        expect(screen.getByLabelText(/Reference/i)).toBeTruthy()
        expect(screen.getByLabelText(/Description/i)).toBeTruthy()
        expect(screen.getByRole('button', {name: /Create Ticket/i})).toBeTruthy()
    })

    it('emits "close" when clicking overlay or Close button', async () => {
        const {emitted} = render(TicketForm, {
            props: {projectName: 'demo', versionId: 'v1'},
        })

        await fireEvent.click(screen.getByText('Close'))
        expect(emitted()['close']).toBeTruthy()

        emitted().close = [] // reset
        const overlay = document.querySelector('.modal-overlay')
        if (!overlay) throw new Error('modal overlay not found in DOM')
        await fireEvent.click(overlay)
        expect(emitted()['close']).toBeTruthy()
    })

    it('submits the form and emits ticket-created', async () => {
        const {emitted} = render(TicketForm, {
            props: {projectName: 'demo', versionId: 'v1'}
        })
        server.use( http.post('http://mock-api/api/v1/projects/demo/versions/v1/tickets', () => {
            return HttpResponse.json({id: 33})
        }))
        await fireEvent.update(screen.getByLabelText(/Reference/i), 'REF123')
        await fireEvent.update(screen.getByLabelText(/Description/i), 'Test ticket')
        await fireEvent.click(screen.getByText('Create Ticket'))

        await waitFor(() => {
            expect(emitted()['ticket-created']).toBeTruthy()
            expect(emitted()['close']).toBeTruthy()
        })
    })

    it('displays error message on failed request', async () => {
        render(TicketForm, {
            props: {projectName: 'demo', versionId: 'v1'}
        })
        server.use( http.post('http://mock-api/api/v1/projects/demo/versions/v1/tickets', () => {
            return HttpResponse.json({detail:'Ticket reference already exits for the project' }, {status: 409})
        }))
        await fireEvent.update(screen.getByLabelText(/Reference/i), 'EXISTING_REF')
        await fireEvent.update(screen.getByLabelText(/Description/i), 'Bad input')
        await fireEvent.click(screen.getByText('Create Ticket'))
        await nextTick();
        await waitFor(() => {
            expect(screen.getByText('Ticket reference already exits for the project')).toBeTruthy();
        });

    })

    it('displays error when required fields are empty', async () => {
        render(TicketForm, {
            props: {projectName: 'demo', versionId: 'v1'}
        })
        await fireEvent.click(screen.getByText('Create Ticket'));
        await nextTick();
        await waitFor(() => {
            expect(screen.getByLabelText(/Reference/i)).toBeInvalid();
        });

        await fireEvent.update(screen.getByTestId('reference'), "New Ticket");
        await fireEvent.click(screen.getByText('Create Ticket'));
        await waitFor(() => {
            expect(screen.getByTestId('reference')).toBeValid();
            expect(screen.getByTestId('description')).toBeInvalid();
        })
    })
})
