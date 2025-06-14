<template>
  <div class="projects-view">
    <h2>Projects</h2>
    <div class="actions">
      <router-link to="/projects/new" class="btn btn-primary">Create New Project</router-link>
    </div>
    <div v-if="projectStore.isLoading" class="loading">Loading projects...</div>
    <div v-if="projectStore.error" class="error-message">{{ projectStore.error }}</div>
    <div v-if="!projectStore.isLoading && !projectStore.error">
      <ul v-if="projectStore.projects.length > 0" class="project-list">
        <li v-for="project in projectStore.projects" :key="project.id || project.name">
          <router-link :to="{ name: 'project-details', params: { id: project.id || project.name } }">
            {{ project.name }}
          </router-link>
          <!-- Add more summary info if available, e.g., project.description -->
        </li>
      </ul>
      <div v-else class="no-data">No projects found.</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useProjectStore } from '../stores/projectStore';

const projectStore = useProjectStore();

onMounted(() => {
  projectStore.fetchProjects();
});
</script>

<style scoped>
.projects-view {
  padding: 20px;
}
.actions {
  margin-bottom: 20px;
}
.btn {
  padding: 10px 15px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 5px;
}
.btn-primary {
  background-color: #007bff;
}
.loading, .error-message, .no-data {
  text-align: center;
  padding: 20px;
}
.error-message { color: red; }
.project-list {
  list-style-type: none;
  padding: 0;
}
.project-list li {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 4px;
}
.project-list li a {
  text-decoration: none;
  color: #333;
  font-weight: bold;
}
</style>
