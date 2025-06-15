<template>
  <div class="project-version-tickets-view">
    <h4>Tickets for Version: {{ versionId }}</h4>

    <div class="actions">
      <button @click="openCreateTicketModal" class="btn btn-sm btn-primary">Add New Ticket</button>
    </div>

    <!-- Create/Edit Ticket Modal -->
    <div v-if="showTicketModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeTicketModal">&times;</span>
        <h5>{{ editingTicket ? 'Edit Ticket' : 'Add New Ticket' }}</h5>
        <form @submit.prevent="handleSaveTicket">
          <div class="form-group">
            <label for="ticketReference">Reference:</label>
            <input type="text" id="ticketReference" v-model="currentTicket.reference" required />
          </div>
          <div class="form-group">
            <label for="ticketDescription">Description:</label>
            <textarea id="ticketDescription" v-model="currentTicket.description" required></textarea>
          </div>
          <div class="form-group">
            <label for="ticketStatus">Status:</label>
            <select id="ticketStatus" v-model="currentTicket.status">
              <!-- Populate with actual status options later from a config or API -->
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="review">In Review</option>
              <option value="closed">Closed</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <div v-if="projectStore.ticketsError" class="error-message">{{ projectStore.ticketsError }}</div>
          <button type="submit" :disabled="projectStore.isTicketsLoading" class="btn btn-success btn-sm">
            {{ projectStore.isTicketsLoading ? 'Saving...' : 'Save Ticket' }}
          </button>
          <button type="button" @click="closeTicketModal" class="btn btn-link btn-sm">Cancel</button>
        </form>
      </div>
    </div>

    <div v-if="projectStore.isTicketsLoading && projectStore.currentVersionTickets.length === 0" class="loading">Loading tickets...</div>
    <div v-if="projectStore.ticketsError && !showTicketModal" class="error-message">{{ projectStore.ticketsError }}</div>

    <table v-if="projectStore.currentVersionTickets.length > 0" class="tickets-table">
      <thead>
        <tr>
          <th>Reference</th>
          <th>Description</th>
          <th>Status</th>
          <th>Created At</th>
          <th>Updated At</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ticket in projectStore.currentVersionTickets" :key="ticket.id">
          <td>{{ ticket.reference }}</td>
          <td>{{ ticket.description }}</td>
          <td>{{ ticket.status }}</td>
          <td>{{ formatDate(ticket.created_at) }}</td>
          <td>{{ formatDate(ticket.updated_at) }}</td>
          <td>
            <button @click="openEditTicketModal(ticket)" class="btn btn-xs btn-info">Edit</button>
            <!-- Add delete button later -->
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!projectStore.isTicketsLoading && projectStore.currentVersionTickets.length === 0 && !projectStore.ticketsError" class="no-data">
      No tickets found for this version. Add one to get started!
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue';
import { useProjectStore } from '../stores/projectStore';
import { useRoute } from 'vue-router';

const projectStore = useProjectStore();
const route = useRoute();
const projectId = computed(() => route.params.id);
const versionId = computed(() => route.params.versionId);

const showTicketModal = ref(false);
const editingTicket = ref(null);
const currentTicket = reactive({
  id: null,
  reference: '',
  description: '',
  status: 'open'
});

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const resetCurrentTicket = () => {
  currentTicket.id = null;
  currentTicket.reference = '';
  currentTicket.description = '';
  currentTicket.status = 'open';
};

const openCreateTicketModal = () => {
  resetCurrentTicket();
  editingTicket.value = null;
  projectStore.ticketsError = null;
  showTicketModal.value = true;
};

const openEditTicketModal = (ticket) => {
  editingTicket.value = ticket;
  currentTicket.id = ticket.id;
  currentTicket.reference = ticket.reference;
  currentTicket.description = ticket.description;
  currentTicket.status = ticket.status;
  projectStore.ticketsError = null;
  showTicketModal.value = true;
};

const closeTicketModal = () => {
  showTicketModal.value = false;
  editingTicket.value = null;
  resetCurrentTicket();
  projectStore.ticketsError = null; // Clear any errors when closing modal
};

const handleSaveTicket = async () => {
  const ticketData = {
    reference: currentTicket.reference,
    description: currentTicket.description,
    status: currentTicket.status
    // Potentially add project_id and version_id if API needs them in body
    // project_id: projectId.value,
    // version_id: versionId.value,
  };
  try {
    if (editingTicket.value) {
      await projectStore.updateTicket(projectId.value, versionId.value, editingTicket.value.id, ticketData);
    } else {
      await projectStore.createTicketInVersion(projectId.value, versionId.value, ticketData);
    }
    closeTicketModal();
    // No explicit re-fetch here, relying on optimistic update in store.
    // If API returns full updated list, could use that.
  } catch (e) {
    // Error is set in the store by action's catch block, and should be displayed in the modal
  }
};

const loadTickets = () => {
    if (projectId.value && versionId.value) {
        projectStore.fetchTicketsForVersion(projectId.value, versionId.value);
    }
};

onMounted(() => {
  loadTickets();
});

// Watch for changes in route params (e.g., navigating between versions)
watch([projectId, versionId], (newValues, oldValues) => {
    if (newValues[0] && newValues[1] && (newValues[0] !== oldValues[0] || newValues[1] !== oldValues[1])) {
        loadTickets();
    }
});

</script>

<style scoped>
.project-version-tickets-view { padding-top: 15px; }
.actions { margin-bottom: 15px; }
.modal {
  position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
  overflow: auto; background-color: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
}
.modal-content {
  background-color: #fefefe; padding: 20px; border: 1px solid #888;
  width: 80%; max-width: 500px; border-radius: 8px; position: relative;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.close {
  color: #aaa; position: absolute; top: 10px; right: 15px;
  font-size: 28px; font-weight: bold; cursor: pointer;
}
.close:hover, .close:focus { color: black; text-decoration: none; }
.form-group { margin-bottom: 10px; }
.form-group label { display: block; margin-bottom: 5px; font-size: 0.9em; font-weight: bold; }
.form-group input, .form-group textarea, .form-group select {
  width: calc(100% - 22px); /* Account for padding and border */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box; /* Include padding and border in the element's total width and height */
}
.form-group textarea { min-height: 80px; resize: vertical; }
.btn-sm { padding: 8px 12px; font-size: 0.9em; }
.btn-xs { padding: 4px 8px; font-size: 0.8em; }
.tickets-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
.tickets-table th, .tickets-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
.tickets-table th { background-color: #f0f0f0; font-weight: bold; }
.loading, .error-message, .no-data { text-align: center; padding: 20px; font-size: 1.1em; }
.error-message { color: #d9534f; /* Bootstrap danger color */ margin-bottom: 10px; }
.no-data { color: #777; }
</style>
