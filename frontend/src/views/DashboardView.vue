<template>
  <div class="dashboard">
    <div v-if="dashboardStore.isLoading" class="loading">Loading dashboard data...</div>
    <div v-if="dashboardStore.error" class="error-message">{{ dashboardStore.error }}</div>
    <div v-if="!dashboardStore.isLoading && !dashboardStore.error">
      <div v-if="dashboardStore.projects.length === 0" class="no-data">
        No projects to display.
      </div>
       <ProjectCard v-for="project in dashboardStore.projects"
        :key="project.name-project.version"
        :projectName = project.name
        :projectVersion = project.version
        :tickets = project.statistics
        :bugs = project.bugs
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useDashboardStore } from '../stores/dashboardStore';
import ProjectCard from '../components/dashboard/ProjectCard.vue';

const dashboardStore = useDashboardStore();

onMounted(() => {
  dashboardStore.fetchDashboardData();
});
</script>

<style scoped>
.dashboard {
  padding: 20px;
}
.loading, .error-message, .no-data {
  text-align: center;
  padding: 20px;
  font-size: 1.2em;
}
.error-message {
  color: red;
}
.project-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 20px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.project-card h3 {
  margin-top: 0;
  color: #333;
}
.versions-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}
.versions-table th, .versions-table td {
  border: 1px solid #eee;
  padding: 8px;
  text-align: left;
}
.versions-table th {
  background-color: #f7f7f7;
  font-weight: bold;
}
</style>
