<template>
  <div v-if="isLoading" class="loading-overlay">
    <div class="spinner" role="status"></div>
  </div>
</template>

<script setup lang="ts">
import { useLoadingStore } from "@/stores/loadingStore"
import { storeToRefs } from "pinia"

const loadingStore = useLoadingStore()
const { isLoading } = storeToRefs(loadingStore)
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.spinner {
  border: 5px solid #f3f3f3;
  border-top: 5px solid #3498db;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
