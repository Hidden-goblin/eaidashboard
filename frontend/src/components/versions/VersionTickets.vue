<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h3>Tickets for Version {{ versionId }}</h3>

      <!-- Tickets List -->
      <div v-if="loading" class="loading">Loading tickets...</div>
      <div v-if="error" class="error">{{ error }}</div>
      <ul v-if="tickets.length">
        <li v-for="ticket in tickets" :key="ticket.reference">
          <strong>{{ ticket.reference }}</strong>: {{ ticket.description }} ({{ ticket.status }})
        </li>
      </ul>
      <div v-else-if="!loading && !error">No tickets found for this version.</div>

      <div class="button-row">
        <BaseButton variant="create" @click="showTicketForm = true">
          Add Ticket
        </BaseButton>
        <BaseButton variant="close" :icon="XMarkIcon" @click="emit('close')">
          Close
        </BaseButton>
      </div>
      <!-- Ticket Form Modal -->
      <TicketForm
          v-if="showTicketForm"
          :projectName="projectName"
          :versionId="versionId"
          @ticket-created="onTicketCreated"
          @close="showTicketForm = false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue';
import TicketForm from '../tickets/TicketForm.vue';
import {useAuthStore} from '@/stores/authStore';
import {useApi} from '@/composables/useApi';
import {useApiBaseUrl} from '@/composables/useApiBaseUrl';
import BaseButton from "../utils/BaseButton.vue";
import {XMarkIcon} from '@heroicons/vue/20/solid';

// Props & Emits
const props = defineProps({
  projectName: {type: String, required: true},
  versionId: {type: [String, Number], required: true}
});
const emit = defineEmits(['close']);

// State
const tickets = ref([]);
const loading = ref(false);
const error = ref('');
const showTicketForm = ref(false);

// API
const authStore = useAuthStore();
const {fetchWithAuth} = useApi();
const apiBaseUrl = useApiBaseUrl();

// Fetch tickets
const fetchTickets = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await fetchWithAuth(
        `${apiBaseUrl}/api/v1/projects/${props.projectName}/versions/${props.versionId}/tickets`,
        {
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
    );

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Failed to load tickets');
    }

    const data = await response.json();
    tickets.value = data;
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

// When ticket is created
const onTicketCreated = () => {
  showTicketForm.value = false;
  fetchTickets(); // refresh after successful ticket creation
};

onMounted(fetchTickets);
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  position: relative;
}

.ticket-list {
  list-style: none;
  padding: 0;
}

.ticket-list li {
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.loading {
  margin-top: 10px;
  font-style: italic;
}

.button-row {
  display: flex;
  justify-content: flex-end; /* ou 'space-between' ou 'center' selon le besoin */
  gap: 10px;
  margin-top: 20px;
}

</style>