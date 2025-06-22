import { onMounted, onBeforeUnmount } from 'vue';

export function useEscapeToClose(onClose) {
  const handleKeydown = (event) => {
    if (event.key === 'Escape') {
      onClose();
    }
  };

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
  });

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleKeydown);
  });
}
