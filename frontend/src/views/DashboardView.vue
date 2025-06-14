<template>
  <div class="dashboard">
    <h2>Dashboard</h2>
    <div v-if="dashboardStore.isLoading" class="loading">Loading dashboard data...</div>
    <div v-if="dashboardStore.error" class="error-message">{{ dashboardStore.error }}</div>
    <div v-if="!dashboardStore.isLoading && !dashboardStore.error">
      <div v-if="dashboardStore.projects.length === 0" class="no-data">
        No projects to display.
      </div>
      <div v-for="project in dashboardStore.projects" :key="project.name" class="project-card">
        <h3>{{ project.name }}</h3>
        <table class="versions-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Status</th>
              <th>Tickets</th>
              <th>Bugs</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="version in project.versions" :key="version.version">
              <td>{{ version.version }}</td>
              <td>{{ version.status }}</td>
              <td>{{ version.tickets }}</td>
              <td>{{ version.bugs }}</td>
            </tr>
            <tr v-if="project.versions.length === 0">
              <td colspan="4">No versions for this project.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useDashboardStore } from '../stores/dashboardStore';

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
