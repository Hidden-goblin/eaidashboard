<!-- src/components/tickets/TicketForm.vue -->
<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content small">
      <h4>Create New Ticket</h4>
      <form @submit.prevent="submitForm">
        <div>
          <label for="reference">Reference</label>
          <input id="reference" v-model="ticket.reference" required />
        </div>
        <div>
          <label for="description">Description</label>
          <textarea id="description" v-model="ticket.description" required></textarea>
        </div>
        <div class="actions">
          <BaseButton variant="create" type="submit">
            Create Ticket
          </BaseButton>
          <BaseButton variant="close" @click="emit('close')">
            Close
          </BaseButton>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useApiBaseUrl } from '../../composables/useApiBaseUrl.js';
import { useAuthStore } from '../../stores/authStore.js';
import { useApi } from '../../composables/useApi.js';
import BaseButton from "../utils/BaseButton.vue";

// Props
const props = defineProps({
  projectName: {
    type: String,
    required: true
  },
  versionId: {
    type: [String, Number],
    required: true
  }
});

// Emit
const emit = defineEmits(['close', 'ticket-created']);

// Setup API tools
const apiBaseUrl = useApiBaseUrl();
const authStore = useAuthStore();
const { fetchWithAuth } = useApi();

// Reactive form data
const ticket = ref({
  reference: '',
  description: '',
  status: 'open',
  created: new Date().toISOString()
});

const error = ref('');

// Form submission
const submitForm = async () => {
  const url = `${apiBaseUrl}/api/v1/projects/${props.projectName}/versions/${props.versionId}/tickets/`;
  try {
    const response = await fetchWithAuth(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`
      },
      body: JSON.stringify(ticket.value)
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Error creating ticket');
    }

    const createdTicket = await response.json();
    emit('ticket-created', createdTicket);
    emit('close');
    resetForm();
  } catch (err) {
    error.value = err.message;
  }
};

// Reset form
const resetForm = () => {
  ticket.value = {
    reference: '',
    description: '',
    status: 'open',
    created: new Date().toISOString()
  };
  error.value = '';
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.modal-content.small {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 400px;
  width: 90%;
}

.btn-primary {
  background: #3490dc;
  color: white;
  padding: 10px;
  border: none;
  margin-top: 10px;
  cursor: pointer;
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
  padding: 10px;
  border: none;
  margin-top: 10px;
  margin-left: 10px;
  cursor: pointer;
}

.error {
  color: red;
  margin-top: 10px;
}

.actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
