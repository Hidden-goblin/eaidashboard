import { reactive } from 'vue'

type AuthEventHandler = () => void

const state = reactive({
    handlers: [] as AuthEventHandler[],
})

export function useAuthEvents() {
    function onUnauthorized(handler: AuthEventHandler): void {
        state.handlers.push(handler)
    }

    function emitUnauthorized(): void {
        state.handlers.forEach((h) => h())
    }

    function clearHandlers(): void {
        state.handlers.length = 0
    }

    return {
        onUnauthorized,
        emitUnauthorized,
        clearHandlers,
    }
}
