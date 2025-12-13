import { render, fireEvent, screen } from '@testing-library/vue'
import LoginModal from '@/components/access/LoginModal.vue'
import { describe, it,  afterEach, vi, expect } from 'vitest'
import { createTestingPinia } from '@pinia/testing'

let mockLogin: (...args: any[]) => Promise<any>

vi.mock('@/stores/authStore', () => ({
    useAuthStore: () => ({
        login: (...args: any[]) => mockLogin(...args)
    })
}))

afterEach(() => vi.clearAllMocks())


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
        mockLogin = vi.fn(async () => Promise.resolve())
        const emailInput = screen.getByTestId('username-input')
        const passwordInput = screen.getByTestId('password-input')

        await fireEvent.update(emailInput, 'john@jon.son')
        await fireEvent.update(passwordInput, 'password123')
        await fireEvent.click(screen.getByText('Connect'))

        await vi.waitFor(() => {
            expect(emitted()['login-success']).toBeTruthy()
        })
    })

    it('shows error on invalid credentials', async () => {
        render(LoginModal, {
            global: {
                plugins: [createTestingPinia()]
            }
        })
        mockLogin = vi.fn(async () => {
            throw new Error('Invalid credentials')
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
        render(LoginModal, {
            global: {
                plugins: [createTestingPinia()]
            }
        })
        mockLogin = vi.fn(async () => {
            throw new Error('Failed to fetch')
        })

        await fireEvent.update(screen.getByLabelText(/email/i), 'valid@example.com')
        await fireEvent.update(screen.getByLabelText(/password/i), 'password123')
        await fireEvent.click(screen.getByText('Connect'))

        expect(await screen.findByText(/Failed to fetch/i)).toBeTruthy()
    })
})
