<template>
  <div class="project-detail-view">
    <div v-if="projectStore.isLoading" class="loading">Loading project details...</div>
    <div v-if="projectStore.error" class="error-message">{{ projectStore.error }}</div>
    <div v-if="projectStore.currentProject && !projectStore.isLoading">
      <h2>Project: {{ projectStore.currentProject.name }}</h2>
      <p>ID: {{ projectStore.currentProject.id || 'N/A' }}</p>
      <p>Description: {{ projectStore.currentProject.description || 'No description provided.' }}</p>

      <!-- Placeholder for tabs/sections (Versions, Bugs, Campaign, Repository) -->
      <nav class="project-tabs">
        <router-link :to="{ name: 'project-versions', params: { id: projectId } }">Versions</router-link>
        <router-link :to="{ name: 'project-bugs', params: { id: projectId } }">Bugs</router-link>
        <router-link :to="{ name: 'project-campaigns', params: { id: projectId } }">Campaigns</router-link>
        <router-link :to="{ name: 'project-repository', params: { id: projectId } }">Repository</router-link>
      </nav>
      <router-view name="projectContent"></router-view> <!-- Named view for nested routes -->
    </div>
    <div v-if="!projectStore.currentProject && !projectStore.isLoading && !projectStore.error" class="no-data">
      Project not found.
    </div>
    <router-link to="/projects" class="btn btn-link">Back to Projects</router-link>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue';
import { useProjectStore } from '../stores/projectStore';
import { useRoute } from 'vue-router';

const projectStore = useProjectStore();
const route = useRoute();
const projectId = computed(() => route.params.id);

onMounted(() => {
  projectStore.fetchProjectDetails(projectId.value);
});
</script>

<style scoped>
.project-detail-view { padding: 20px; }
.loading, .error-message, .no-data { text-align: center; padding: 20px; }
.error-message { color: red; }
.project-tabs {
  margin-top: 20px;
  margin-bottom: 20px;
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
}
.project-tabs a {
  margin-right: 15px;
  text-decoration: none;
  color: #007bff;
  font-weight: bold;
}
.project-tabs a.router-link-exact-active {
  border-bottom: 2px solid #007bff;
}
.btn-link {
  display: inline-block;
  margin-top: 20px;
}
</style>
