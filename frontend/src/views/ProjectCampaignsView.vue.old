<template>
  <div class="project-campaigns-view">
    <h4>Campaigns</h4>
    <div class="actions">
      <button @click="openCreateCampaignModal" class="btn btn-sm btn-primary">New Campaign</button>
    </div>

    <!-- Create Campaign Modal -->
    <div v-if="showCreateCampaignModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeCreateCampaignModal">&times;</span>
        <h5>Create New Campaign</h5>
        <form @submit.prevent="handleCreateCampaign">
          <div class="form-group">
            <label for="campaignName">Campaign Name (Optional):</label>
            <input type="text" id="campaignName" v-model="newCampaign.name" />
          </div>
          <div class="form-group">
            <label for="campaignVersion">Target Version:</label>
            <select id="campaignVersion" v-model="newCampaign.version" required>
              <option disabled value="">Select version</option>
              <option v-for="version in projectStore.currentProject?.versions"
                      :key="version.id || version.version"
                      :value="version.version"> <!-- Ensure value is what API expects, e.g. version name/number or ID -->
                {{ version.version }} (Status: {{version.status}})
              </option>
            </select>
          </div>
          <!-- Add other fields like 'description', 'start_date', 'end_date' -->
          <div v-if="projectStore.campaignsError" class="error-message">{{ projectStore.campaignsError }}</div>
          <button type="submit" :disabled="projectStore.isCampaignsLoading" class="btn btn-success btn-sm">
            {{ projectStore.isCampaignsLoading ? 'Creating...' : 'Create Campaign' }}
          </button>
          <button type="button" @click="closeCreateCampaignModal" class="btn btn-link btn-sm">Cancel</button>
        </form>
      </div>
    </div>

    <div v-if="projectStore.isCampaignsLoading && projectStore.projectCampaigns.length === 0" class="loading">Loading campaigns...</div>
    <div v-if="projectStore.campaignsError && !showCreateCampaignModal" class="error-message">{{ projectStore.campaignsError }}</div>

    <table v-if="projectStore.projectCampaigns.length > 0" class="campaigns-table">
      <thead>
        <tr>
          <th>Name / ID</th>
          <th>Version</th>
          <th>Status</th>
          <th>Occurrence</th>
          <th>Created At</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="campaign in projectStore.projectCampaigns" :key="campaign.id">
          <td>{{ campaign.name || campaign.id }}</td>
          <td>{{ campaign.version }}</td> <!-- Assuming campaign object has 'version' property -->
          <td>{{ campaign.status || 'N/A' }}</td>
          <td>{{ campaign.occurrence || 'N/A' }}</td>
          <td>{{ formatDate(campaign.created_at) }}</td>
          <td>
            <router-link :to="{ name: 'project-campaign-board', params: { id: projectId, campaignId: campaign.id } }" class="btn btn-xs btn-info">
              View Board
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!projectStore.isCampaignsLoading && projectStore.projectCampaigns.length === 0 && !projectStore.campaignsError" class="no-data">
      No campaigns found for this project.
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

const showCreateCampaignModal = ref(false);
const newCampaign = reactive({ name: '', version: '' });

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const setDefaultNewCampaignVersion = () => {
    if (projectStore.currentProject?.versions?.length > 0) {
        newCampaign.version = projectStore.currentProject.versions[0].version;
    } else {
        newCampaign.version = ''; // No versions available
    }
};

const openCreateCampaignModal = () => {
  projectStore.campaignsError = null; // Clear previous errors
  setDefaultNewCampaignVersion(); // Set default version when opening
  showCreateCampaignModal.value = true;
};

const closeCreateCampaignModal = () => {
  showCreateCampaignModal.value = false;
  newCampaign.name = '';
  setDefaultNewCampaignVersion(); // Reset to default on close
  projectStore.campaignsError = null;
};

const handleCreateCampaign = async () => {
  if (!newCampaign.version) {
    projectStore.campaignsError = "Target version is required.";
    return;
  }
  try {
    // Ensure campaignData matches what API expects, e.g. if version should be id or name
    await projectStore.createCampaign(projectId.value, { ...newCampaign });
    closeCreateCampaignModal();
    projectStore.fetchCampaignsForProject(projectId.value); // Refresh list
  } catch (e) { /* error should be set in store and displayed in modal */ }
};

const ensureProjectDataAndLoadCampaigns = async () => {
    if (!projectId.value) return;

    // Ensure current project details (especially versions for form) are loaded
    if (!projectStore.currentProject || projectStore.currentProject.id !== projectId.value) {
        await projectStore.fetchProjectDetails(projectId.value);
    }

    // If versions are not part of project details or not yet loaded for current project
    if (projectStore.currentProject && (!projectStore.currentProject.versions || projectStore.currentProject.versions.length === 0)) {
        if (!projectStore.isVersionsLoading) { // Avoid race conditions
            await projectStore.fetchProjectVersions(projectId.value);
        }
    }

    setDefaultNewCampaignVersion(); // Set default for the form after versions are potentially loaded
    projectStore.fetchCampaignsForProject(projectId.value); // Load campaigns
};


onMounted(() => {
  ensureProjectDataAndLoadCampaigns();
});

watch(() => projectId.value, (newId, oldId) => {
    if (newId && newId !== oldId) {
        ensureProjectDataAndLoadCampaigns();
    }
});

// Watch for changes in versions list to update default in form
watch(() => projectStore.currentProject?.versions, (newVersions) => {
    if (showCreateCampaignModal.value || !newCampaign.version) { // Update if modal is open or version not set
       if (newVersions?.length > 0 && (!newCampaign.version || !newVersions.find(v => v.version === newCampaign.version))) {
            newCampaign.version = newVersions[0].version;
       } else if (!newVersions || newVersions.length === 0) {
            newCampaign.version = ''; // No versions available
       }
    }
}, { deep: true });

</script>

<style scoped>
.project-campaigns-view { padding-top: 15px; }
.actions { margin-bottom: 15px; }
.modal {
  position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
  overflow: auto; background-color: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
}
.modal-content {
  background-color: #fefefe; padding: 20px; border: 1px solid #888;
  width: 80%; max-width: 550px; border-radius: 8px; position: relative;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.close {
  color: #aaa; position: absolute; top: 10px; right: 15px;
  font-size: 28px; font-weight: bold; cursor: pointer;
}
.close:hover, .close:focus { color: black; text-decoration: none; }
.form-group { margin-bottom: 10px; }
.form-group label { display: block; margin-bottom: 5px; font-size: 0.9em; font-weight: bold; }
.form-group input, .form-group select {
  width: calc(100% - 22px); padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;
}
.campaigns-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
.campaigns-table th, .campaigns-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
.campaigns-table th { background-color: #f0f0f0; font-weight: bold; }
.loading, .error-message, .no-data { text-align: center; padding: 20px; font-size: 1.1em; }
.error-message { color: #d9534f; margin-bottom: 10px; }
.no-data { color: #777; }
.btn-sm { padding: 8px 12px; font-size: 0.9em; }
.btn-xs { padding: 4px 8px; font-size: 0.8em; }
.btn-link { background-color: transparent; color: #007bff; text-decoration: underline; border: none; }
</style>
