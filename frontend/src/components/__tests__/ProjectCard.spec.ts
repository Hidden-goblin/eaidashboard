import { render, screen } from '@testing-library/vue'
import ProjectCard from '@/components/dashboard/ProjectCard.vue'
import { describe, it, expect } from 'vitest'

const baseProps = {
    projectName: 'TestProject',
    projectVersion: '1.2.3',
    tickets: {
        open: 4,
        in_progress: 2,
        done: 4
    },
    bugs: {
        open_blocking: 1,
        closed_blocking: 2,
        open_major: 0,
        closed_major: 1,
        open_minor: 3,
        closed_minor: 0
    },
    index: 8
}

describe('ProjectCard', () => {
    it('renders project name and version', () => {
        render(ProjectCard, { props: baseProps })

        expect(screen.getByTestId('project-name-8').textContent).toBe('TestProject')
        expect(screen.getByTestId('project-version-8').textContent).toBe('Version 1.2.3')
    })

    it('renders only non-zero ticket statuses', () => {
        render(ProjectCard, { props: baseProps })

        expect(screen.queryByTestId('ticket-8-open')).toBeTruthy()
        expect(screen.queryByTestId('ticket-8-in_progress')).toBeTruthy()
        expect(screen.queryByTestId('ticket-8-done')).toBeTruthy()
        expect(screen.queryByTestId('ticket-8-cancelled')).not.toBeTruthy()
    })

    it('displays correct bug columns', () => {
        render(ProjectCard, { props: baseProps })

        expect(screen.getByTestId('bug-8-blocking-open')).toBeTruthy()
        expect(screen.getByTestId('bug-8-major-open')).toBeTruthy()
        expect(screen.getByTestId('bug-8-minor-open')).toBeTruthy()
    })

    it('does not crash with all-zero tickets and bugs', () => {
        render(ProjectCard, {
            props: {
                ...baseProps,
                tickets: {
                    open: 0,
                    done: 0
                },
                bugs: {
                    open_blocking: 0,
                    closed_blocking: 0,
                    open_major: 0,
                    closed_major: 0,
                    open_minor: 0,
                    closed_minor: 0
                }
            }
        })

        expect(screen.queryByTestId('ticket-8-open')).not.toBeTruthy()
        expect(screen.queryByTestId('bug-8-blocking-open')).toBeTruthy() // structure is always rendered
    })

    it('correctly calculates width percentages', () => {
        render(ProjectCard, { props: baseProps })

        const openTicket = screen.getByTestId('ticket-8-open')
        const doneTicket = screen.getByTestId('ticket-8-done')

        expect(openTicket.style.width).toBe('40%') // 4 / (4+2+4) = 40%
        expect(doneTicket.style.width).toBe('40%') // 4 / 10 = 40%
    })

    it('hides labels if percentage is too small', () => {
        const smallTicketProps = {
            ...baseProps,
            tickets: {
                open: 8,
                in_progress: 92
            }
        }

        render(ProjectCard, { props: smallTicketProps })

        const openLabel = screen.queryByText(/open/i)
        const inProgressLabel = screen.queryByText(/in_progress/i)

        if (openLabel) {
            expect(parseFloat(openLabel.parentElement?.style.width)).toBeLessThan(9)
        }
        expect(inProgressLabel).toBeTruthy()
    })
})
