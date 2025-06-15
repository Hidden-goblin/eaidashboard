<template>
  <div class="project-versions-view">
    <h4>Versions</h4>
    <div class="actions">
      <!-- Button to open a modal or navigate to a new version form -->
      <button @click="showAddVersionForm = true" class="btn btn-sm btn-primary">Add New Version</button>
    </div>

    <!-- Add Version Form (Modal or inline) -->
    <div v-if="showAddVersionForm" class="add-version-form">
      <h5>Add Version</h5>
      <form @submit.prevent="handleCreateVersion">
        <div class="form-group">
          <label for="versionName">Version Name/Number:</label>
          <input type="text" id="versionName" v-model="newVersionName" required />
        </div>
        <!-- Add other fields like start_date, end_date if needed -->
        <div v-if="projectStore.versionsError" class="error-message">{{ projectStore.versionsError }}</div>
        <button type="submit" :disabled="projectStore.isVersionsLoading" class="btn btn-success btn-sm">
          {{ projectStore.isVersionsLoading ? 'Creating...' : 'Create Version' }}
        </button>
        <button type="button" @click="showAddVersionForm = false; projectStore.versionsError = null;" class="btn btn-link btn-sm">Cancel</button>
      </form>
    </div>

    <div v-if="projectStore.isVersionsLoading && (!projectStore.currentProject || !projectStore.currentProject.versions || projectStore.currentProject.versions.length === 0)" class="loading">Loading versions...</div>
    <div v-if="projectStore.versionsError && !showAddVersionForm" class="error-message">{{ projectStore.versionsError }}</div>

    <table v-if="projectStore.currentProject && projectStore.currentProject.versions && projectStore.currentProject.versions.length > 0" class="versions-table">
      <thead>
        <tr>
          <th>Version</th>
          <th>Status</th>
          <th>Start Date</th>
          <th>End Date Forecast</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="version in projectStore.currentProject.versions" :key="version.id || version.version">
          <td>{{ version.version || version.name }}</td> <!-- Handle if API uses 'name' or 'version' -->
          <td>{{ version.status || 'N/A' }}</td>
          <td>{{ formatDate(version.start_date) || 'N/A' }}</td>
          <td>{{ formatDate(version.end_date_forecast) || 'N/A' }}</td>
          <td>
            <router-link :to="{ name: 'project-version-tickets', params: { id: projectId, versionId: version.id || version.version || version.name } }" class="btn btn-xs btn-info">View Tickets</router-link>
            <!-- Add edit/delete buttons later -->
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="projectStore.currentProject && projectStore.currentProject.versions && projectStore.currentProject.versions.length === 0 && !projectStore.isVersionsLoading && !projectStore.versionsError" class="no-data">
      No versions found for this project. Create one to get started!
    </div>
     <div v-if="!projectStore.currentProject && !projectStore.isLoading && !projectStore.error" class="no-data">
      Project data not available. Cannot display versions.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useProjectStore } from '../stores/projectStore';
import { useRoute } from 'vue-router';

const projectStore = useProjectStore();
const route = useRoute();
const projectId = computed(() => route.params.id);

const showAddVersionForm = ref(false);
const newVersionName = ref('');

const formatDate = (dateString) => {
  if (!dateString) return null;
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const handleCreateVersion = async () => {
  if (!newVersionName.value.trim()) {
    projectStore.versionsError = "Version name cannot be empty."; // Use specific error state
    return;
  }
  try {
    await projectStore.createProjectVersion(projectId.value, { version: newVersionName.value }); // Ensure API expects {version: ...}
    newVersionName.value = '';
    showAddVersionForm.value = false;
    projectStore.versionsError = null; // Clear error on success
  } catch (e) {
    // Error is already set in store by createProjectVersion action's catch block
  }
};

// Function to load project details and/or versions
const loadData = async () => {
  if (!projectId.value) return;

  // Ensure current project context is set
  if (!projectStore.currentProject || projectStore.currentProject.id !== projectId.value) {
    await projectStore.fetchProjectDetails(projectId.value);
  }

  // If versions are not populated by fetchProjectDetails or need a separate call
  // (e.g., if currentProject exists but versions array is missing or empty)
  // This also handles re-fetching if directly navigating to versions tab.
  if (projectStore.currentProject && projectStore.currentProject.id === projectId.value) {
    if (!projectStore.currentProject.versions || projectStore.currentProject.versions.length === 0) {
       // Check if versions were perhaps fetched but resulted in empty and there's no error
       // Avoid re-fetching if already loaded and genuinely empty.
       // This logic might need refinement based on how API indicates "fetched but empty" vs "not fetched".
       // For now, if versions array is empty and no loading/error state indicates an ongoing/failed fetch, try fetching.
      if(!projectStore.isVersionsLoading && !projectStore.versionsError) {
        await projectStore.fetchProjectVersions(projectId.value);
      }
    }
  }
};

onMounted(() => {
  loadData();
});

// Watch for route changes if a user navigates between projects while on a versions tab
// This might be less common if ProjectDetailView handles the parent project loading
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadData();
  }
});

</script>

<style scoped>
.project-versions-view { padding-top: 15px; }
.actions { margin-bottom: 15px; }
.add-version-form {
  background-color: #f9f9f9;
  padding: 15px;
  border-radius: 5px;
  margin-bottom: 20px;
  border: 1px solid #eee;
}
.add-version-form h5 { margin-top: 0; }
.form-group { margin-bottom: 10px; }
.form-group label { display: block; margin-bottom: 5px; font-size: 0.9em; }
.form-group input { width: calc(100% - 20px); padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
.btn-sm { padding: 5px 10px; font-size: 0.85em; }
.btn-xs { padding: 3px 8px; font-size: 0.75em; }
.versions-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
.versions-table th, .versions-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.versions-table th { background-color: #f0f0f0; }
.loading, .error-message, .no-data { text-align: center; padding: 15px; }
.error-message { color: red; }
</style>
