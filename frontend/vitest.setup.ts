import { beforeAll, afterEach, afterAll } from 'vitest'
import { server } from '@/mocks/node.js'
import '@testing-library/jest-dom'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())