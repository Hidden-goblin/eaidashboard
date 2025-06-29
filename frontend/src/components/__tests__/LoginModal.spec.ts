import { render, fireEvent, screen, waitFor } from '@testing-library/vue'
import LoginModal from '@/components/access/LoginModal.vue'
import { describe, it, beforeAll, afterAll, afterEach, vi, expect } from 'vitest'
import { server } from '@/mocks/node'
import { createTestingPinia } from '@pinia/testing'
import { http, HttpResponse } from 'msw'

vi.mock('@/composables/useApiBaseUrl', () => ({
    useApiBaseUrl: () => 'http://mock-api'
}))

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('LoginModal', () => {
    it('renders the modal with email, password, connect, cancel', () => {
        render(LoginModal, {
            global: {
                plugins: [createTestingPinia()]
            }
        })
        expect(screen.getByLabelText(/email/i)).toBeTruthy()
        expect(screen.getByLabelText(/password/i)).toBeTruthy()
        expect(screen.getByText(/connect/i)).toBeTruthy()
        expect(screen.getByText(/cancel/i)).toBeTruthy()
    })


    it('logs in successfully and emits login-success', async () => {
        const { emitted } = render(LoginModal, {
            global: {
                plugins: [createTestingPinia()]
            }
        })

        const emailInput = screen.getByTestId('username-input')
        const passwordInput = screen.getByTestId('password-input')

        await fireEvent.update(emailInput, 'valid@example.com')
        await fireEvent.update(passwordInput, 'password123')
        await fireEvent.click(screen.getByText('Connect'))

        await vi.waitFor(() => {
            expect(emitted()).toHaveProperty('login-success')
        })
    })

    it('shows error on invalid credentials', async () => {
        render(LoginModal, {
            global: {
                plugins: [createTestingPinia()]
            }
        })

        await fireEvent.update(screen.getByLabelText(/email/i), 'wrong@example.com')
        await fireEvent.update(screen.getByLabelText(/password/i), 'wrongpass')
        await fireEvent.click(screen.getByText('Connect'))

        expect(await screen.findByText(/invalid credentials/i)).toBeTruthy()
    })

    it('emits close when cancel button is clicked', async () => {
        const {emitted } = render(LoginModal, {
            global: {
                plugins: [createTestingPinia()]
            }
        })

        await fireEvent.click(screen.getByText('Cancel'))
        expect(emitted()).toHaveProperty('close')
    })

    it('handles network errors gracefully', async () => {
        server.use(
            // Simulate network failure
            http.post('http://mock-api/api/v1/token',  async () => {
                return HttpResponse.error()
            })
        )

        render(LoginModal, {
            global: {
                plugins: [createTestingPinia()]
            }
        })

        await fireEvent.update(screen.getByLabelText(/email/i), 'valid@example.com')
        await fireEvent.update(screen.getByLabelText(/password/i), 'password123')
        await fireEvent.click(screen.getByText('Connect'))

        expect(await screen.findByText(/Failed to fetch/i)).toBeTruthy()
    })
})
