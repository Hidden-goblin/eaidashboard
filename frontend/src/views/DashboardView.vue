<template>
  <div class="dashboard">
    <div v-if="dashboardStore.projects.length === 0 && dashboardStore.isLoading" class="loading">
      Loading dashboard data...
    </div>

    <div v-if="dashboardStore.error" class="error-message">{{ dashboardStore.error }}</div>

    <div v-if="!dashboardStore.error">
      <ProjectCard
          v-for="(project, index) in dashboardStore.projects"
          :key="project.name + index"
          :projectName="project.name"
          :projectVersion="project.version"
          :tickets="project.statistics"
          :bugs="project.bugs"
          :index="index"
      />

      <div v-if="dashboardStore.isLoading" class="loading">Loading more projects...</div>
      <div v-if="!dashboardStore.hasMore()" class="end-message">You’ve reached the end.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import {storeToRefs} from 'pinia';
import { useDashboardStore } from '@/stores/dashboardStore';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import ProjectCard from '@/components/dashboard/ProjectCard.vue';

const dashboardStore = useDashboardStore();
const {isLoading} = storeToRefs(useDashboardStore);

onMounted(() => {
  dashboardStore.fetchDashboardData(true);
});

useInfiniteScroll(() => {
  if (!isLoading && dashboardStore.hasMore()) {
    dashboardStore.fetchDashboardData();
  }
});
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.loading,
.error-message,
.end-message {
  text-align: center;
  padding: 20px;
  font-size: 1.2em;
}

.error-message {
  color: red;
}

.end-message {
  color: #888;
}
</style>
