<template>
  <div class="project-campaign-board-view">
    <div v-if="projectStore.isCampaignsLoading && !projectStore.currentCampaign" class="loading">Loading campaign details...</div>
    <div v-if="projectStore.campaignsError && !projectStore.currentCampaign" class="error-message">
      Error loading campaign: {{ projectStore.campaignsError }}
    </div>

    <div v-if="projectStore.currentCampaign">
      <h3>Campaign: {{ projectStore.currentCampaign.name || projectStore.currentCampaign.id }}</h3>
      <p><strong>Project ID:</strong> {{ projectId }}</p>
      <p><strong>Campaign ID:</strong> {{ campaignId }}</p>
      <p><strong>Version:</strong> {{ projectStore.currentCampaign.version }}</p>
      <p><strong>Status:</strong> {{ projectStore.currentCampaign.status || 'N/A' }}</p>
      <p><strong>Occurrence:</strong> {{ projectStore.currentCampaign.occurrence || 'N/A' }}</p>
      <p><strong>Created At:</strong> {{ formatDate(projectStore.currentCampaign.created_at) }}</p>
      <p><strong>Description:</strong> {{ projectStore.currentCampaign.description || 'No description provided.' }}</p>

      <hr />
      <h4>Campaign Board</h4>
      <p><em>Full campaign board functionality (tickets, scenarios, progress tracking) will be implemented here.</em></p>
      <!-- This area will later display tickets associated with the campaign, possibly in a Kanban or list format -->

      <router-link :to="{ name: 'project-campaigns', params: { id: projectId } }" class="btn btn-link btn-sm">Back to Campaigns List</router-link>
    </div>

    <div v-if="!projectStore.isCampaignsLoading && !projectStore.currentCampaign && !projectStore.campaignsError" class="no-data">
      Campaign details could not be loaded or campaign not found.
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed, watch } from 'vue';
import { useProjectStore } from '../stores/projectStore';
import { useRoute } from 'vue-router';

const projectStore = useProjectStore();
const route = useRoute();
const projectId = computed(() => route.params.id);
const campaignId = computed(() => route.params.campaignId);

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const loadCampaignDetails = () => {
    if (projectId.value && campaignId.value) {
        projectStore.fetchCampaignDetails(projectId.value, campaignId.value);
    }
};

onMounted(() => {
  loadCampaignDetails();
});

// Watch for changes in route params if navigating between different campaigns directly
watch([projectId, campaignId], (newVal, oldVal) => {
    if (newVal[0] && newVal[1] && (newVal[0] !== oldVal[0] || newVal[1] !== oldVal[1])) {
        loadCampaignDetails();
    }
});

</script>

<style scoped>
.project-campaign-board-view { padding: 20px; }
.loading, .error-message, .no-data { text-align: center; padding: 20px; font-size: 1.1em; }
.error-message { color: #d9534f; }
.no-data { color: #777; }
h3 { margin-bottom: 15px; }
p { margin-bottom: 8px; }
hr { margin-top: 20px; margin-bottom: 20px; }
.btn-link { display: inline-block; margin-top: 15px; text-decoration: underline;}
</style>
