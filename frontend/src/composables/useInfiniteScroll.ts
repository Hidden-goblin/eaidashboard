// composables/useInfiniteScroll.ts
import { onMounted, onUnmounted } from 'vue';

function throttle(fn: () => void, wait: number) {
    let lastTime = 0;
    return () => {
        const now = Date.now();
        if (now - lastTime >= wait) {
            lastTime = now;
            fn();
        }
    };
}

export function useInfiniteScroll(callback: () => void, distanceFromBottom = 300, throttleMs = 200) {
    const handleScroll = throttle(() => {
        const scrollTop = window.scrollY;
        const viewportHeight = window.innerHeight;
        const fullHeight = document.documentElement.scrollHeight;

        if (scrollTop + viewportHeight + distanceFromBottom >= fullHeight) {
            callback();
        }
    }, throttleMs);

    onMounted(() => {
        window.addEventListener('scroll', handleScroll);
    });

    onUnmounted(() => {
        window.removeEventListener('scroll', handleScroll);
    });
}
