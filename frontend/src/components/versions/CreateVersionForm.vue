<!-- src/components/versions/CreateVersionForm.vue -->
<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h3>Create New Version</h3>
      <form @submit.prevent="createVersion">
        <div class="form-group">
          <label for="versionName">Version Name:</label>
          <input
              type="text"
              id="versionName"
              data-testid="versionNameInput"
              v-model="versionName"
              required
              placeholder="Enter version name"
          />
        </div>
        <div v-if="error" class="error" data-testid="errorVersionForm">{{ error }}</div>
        <div class="actions">
          <BaseButton variant="create" type="submit" data-testid="createVersionButton">Create</BaseButton>
          <BaseButton variant="close" @click="closeModal" data-testid="cancelCreateVersionButton">Cancel</BaseButton>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref} from "vue"
import {useAuthStore} from "@/stores/authStore"
import {useApi} from "@/composables/useApi"
import {useApiBaseUrl} from "@/composables/useApiBaseUrl"
import {useLoadingStore} from "@/stores/loadingStore";
import {logger} from "@/composables/logger";
import { useEscapeToClose } from '@/composables/useEscapteToClose';
import BaseButton from "@/components/utils/BaseButton.vue";


// ✅ define props & emits in <script setup>
const props = defineProps({
  projectName: {
    type: String,
    required: true
  }
});

const emit = defineEmits(["close", "version-created"]);

const closeModal = () => emit('close');
useEscapeToClose(closeModal);

const versionName = ref("");
const error = ref("");

const authStore = useAuthStore();
const {fetchWithAuth} = useApi();
const apiBaseUrl = useApiBaseUrl();

const loadingStore = useLoadingStore();

const createVersion = async () => {
  logger.debug("Entering create version");
  loadingStore.startLoading();
  error.value = "";
  // await loadingStore.withLoading(async () => {
    logger.debug("Entering create version");
    const url = `${apiBaseUrl}/api/v1/projects/${props.projectName}/versions`
    logger.debug('url', url);

    try {
      // 1. POST new version
      const response = await fetchWithAuth(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({version: versionName.value}),
      })

      logger.debug(`Version ${versionName.value} created`);
      // 2. Fetch version details
      const detailsResponse = await fetchWithAuth(`${url}/${versionName.value}`, {
        method: "GET",
      })

      logger.debug(`Version ${versionName.value} retrieved`);
      const data = await detailsResponse.json()

      // emit and reset
      emit("version-created", data)
      versionName.value = ""
      logger.debug(`End of CreateVersion`);
    } catch (err: any) {
      error.value = err.message
    } finally {
      loadingStore.stopLoading();
    }

  // })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

button {
  padding: 8px 16px;
  border: none;
  background: #3498db;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}

button[type='button'] {
  background: #ccc;
}

button:hover {
  opacity: 0.9;
}

.error {
  color: red;
  margin-top: 10px;
}
</style>
