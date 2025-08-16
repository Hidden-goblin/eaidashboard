import { defineStore } from "pinia"
import { ref, computed } from "vue"
import {logger} from "@/composables/logger";

export const useLoadingStore = defineStore("loading", () => {
    const activeRequests = ref(0)

    const isLoading = computed(() => activeRequests.value > 0)

    function startLoading() {
        activeRequests.value++
    }

    function stopLoading() {
        if (activeRequests.value > 0) {
            activeRequests.value--
        }
    }

    async function withLoading<T>(fn: () => Promise<T>): Promise<T>{
        logger.debug("Entering with loading...")
        startLoading()
        try {
            return fn()
        } finally {
            stopLoading()
            logger.debug("... exiting loading...")
        }
    }

    return { isLoading, withLoading, startLoading, stopLoading }
})
