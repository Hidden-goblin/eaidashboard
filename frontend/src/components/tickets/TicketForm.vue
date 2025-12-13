<!-- src/components/tickets/TicketForm.vue -->
<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content small">
      <h4>Create New Ticket</h4>
      <form @submit.prevent="submitForm">
        <div>
          <label for="reference">Reference</label>
          <input id="reference" data-testId="reference" v-model="ticket.reference" required />
        </div>
        <div>
          <label for="description">Description</label>
          <textarea id="description" data-testId="description" v-model="ticket.description" required></textarea>
        </div>
        <div class="actions">
          <BaseButton variant="create" type="submit">
            Create Ticket
          </BaseButton>
          <BaseButton variant="close" @click="emit('close')">
            Close
          </BaseButton>
        </div>
        <div v-if="errorMessage" class="error">{{ errorMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useApiBaseUrl } from '@/composables/useApiBaseUrl';
import { useAuthStore } from '@/stores/authStore';
import { useApi } from '@/composables/useApi';
import BaseButton from "@/components/utils/BaseButton.vue";
import {logger} from "@/composables/logger";

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
const { fetchWithAuth } = useApi();

// Reactive form data
const ticket = ref({
  reference: '',
  description: '',
  status: 'open',
  created: new Date().toISOString()
});

const errorMessage = ref('');

// Form submission
const submitForm = async () => {

  const url = `${apiBaseUrl}/api/v1/projects/${props.projectName}/versions/${props.versionId}/tickets/`;
  try {
    if (!ticket.value.reference || !ticket.value.description) {
      logger.debug(ticket.value);
      throw new Error("Mandatory fields are required");
    }
    const response = await fetchWithAuth(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(ticket.value)
    });

    const createdTicket = await response.json();
    emit('ticket-created', createdTicket);
    emit('close');
    resetForm();
  } catch (err) {
    logger.debug('message', err.message);
    errorMessage.value = `${err?.message}` || 'Unkown error';
    logger.debug('error status',errorMessage.value);
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
  errorMessage.value = '';
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
