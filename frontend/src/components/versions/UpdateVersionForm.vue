<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <h3>Update version {{ activeVersionId }}</h3>
      <form @submit.prevent="updateVersion">
        <div class="form-group">
          <label for="versionStatus">Version Status:</label>
          <select id="versionStatus" data-testid="versionStatus" v-model="versionStatus">
            <option v-for="status in possibleStatuses" :key="status" :value="status">
              {{ status }}
            </option>
          </select>

          <label for="versionStartedInput">Start Date:</label>
          <input type="date" id="versionStartedInput" data-testid="versionStartedInput" v-model="versionStarted" />

          <label for="versionForecastInput">End Forecast:</label>
          <input type="date" id="versionForecastInput" data-testid="versionForecastInput" v-model="versionForecast" />
        </div>
        <div v-if="error" class="error" data-testid="versionErrorMessage">{{ error }}</div>
        <div class="actions">
          <BaseButton variant="update" type="submit" data-testid="versionSubmitButton">Update</BaseButton>
          <BaseButton variant="close" @click="closeModal" data-testid="versionCancelButton">Cancel</BaseButton>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useApiBaseUrl } from '@/composables/useApiBaseUrl';
import { useApi } from '@/composables/useApi';
import { useEscapeToClose } from '@/composables/useEscapteToClose';
import { useAuthStore } from '@/stores/authStore';
import { logger } from "@/composables/logger";
import BaseButton from "@/components/utils/BaseButton.vue";
import {useLoadingStore} from "@/stores/loadingStore";


const { projectName, activeVersionId } = defineProps({
  projectName: { type: String, required: true },
  activeVersionId: { type: String, required: true }
});

const emit = defineEmits(['close', 'version-updated']);

const apiBaseUrl = useApiBaseUrl();
const { fetchWithAuth } = useApi();
const authStore = useAuthStore();
const loadingStore = useLoadingStore();

const versionStatus = ref('');
const versionStarted = ref('');
const versionForecast = ref('');
const possibleStatuses = ref([]);
const error = ref('');

const closeModal = () => emit('close');
useEscapeToClose(closeModal);

const fetchPossibleStatuses = async (currentStatus) => {
  try {
    const response = await fetchWithAuth(
      `${apiBaseUrl}/api/v1/settings/projects/${projectName}/workflow/${currentStatus}`,
      {
        method: 'GET'
      }
    );

    const data = await response.json();
    const statuses = data.data ?? [];
    statuses.unshift(currentStatus);
    possibleStatuses.value = statuses;
  } catch (err) {
    logger.debug("In fetch statues");
    logger.error(err);
    throw new Error('Error fetching status workflow');
  }
};

const fetchVersionData = async () => {
  loadingStore.startLoading();
  try {
    const response = await fetchWithAuth(
      `${apiBaseUrl}/api/v1/projects/${projectName}/versions/${activeVersionId}`,
      {
        method: 'GET'
      }
    );

    const data = await response.json();

    versionStatus.value = data.status;
    versionStarted.value = data.started?.slice(0, 10) ?? '';
    versionForecast.value = data.end_forecast?.slice(0, 10) ?? '';

    await fetchPossibleStatuses(data.status);
  } catch (err) {
    logger.debug("In fetch data");
    logger.error(err);
    error.value = err.message;
  } finally {
    loadingStore.stopLoading()
  }
};

const updateVersion = async () => {
  loadingStore.startLoading();
  try {
    const bodyData = {
      started: versionStarted.value === '' ? null : versionStarted.value,
      end_forecast: versionForecast.value === '' ? null : versionForecast.value,
      status: versionStatus.value
    };

    if (versionStarted.value && versionForecast.value && versionStarted.value > versionForecast.value) {
      throw new Error( "Start date cannot be after end forecast");
    }

    await fetchWithAuth(
      `${apiBaseUrl}/api/v1/projects/${projectName}/versions/${activeVersionId}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bodyData)
      }
    );

    emit('version-updated', 1);
  } catch (err) {
    error.value = err.message;
  } finally {
    loadingStore.stopLoading();
  }
};

onMounted(fetchVersionData);
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

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
  margin-bottom: 10px;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.error {
  color: red;
  margin-top: 10px;
}
</style>
