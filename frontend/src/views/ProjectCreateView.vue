<template>
  <div class="project-create-view">
    <h2>Create New Project</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="projectName">Project Name:</label>
        <input type="text" id="projectName" v-model="projectName" required />
      </div>
      <!-- Add other fields if necessary, e.g., description -->
      <div v-if="projectStore.error" class="error-message">{{ projectStore.error }}</div>
      <button type="submit" :disabled="projectStore.isLoading" class="btn btn-success">
        {{ projectStore.isLoading ? 'Creating...' : 'Create Project' }}
      </button>
      <router-link to="/projects" class="btn btn-link">Cancel</router-link>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useProjectStore } from '../stores/projectStore';
import { useRouter } from 'vue-router';

const projectStore = useProjectStore();
const router = useRouter();
const projectName = ref('');

const handleSubmit = async () => {
  if (!projectName.value.trim()) {
    projectStore.error = "Project name cannot be empty.";
    return;
  }
  try {
    await projectStore.createProject({ name: projectName.value });
    // Assuming API returns the created project or success, then navigate
    router.push('/projects');
  } catch (e) {
    // Error is already set in store, or handle specific form error display
    console.error("Failed to create project:", e);
  }
};
</script>

<style scoped>
.project-create-view {
  max-width: 500px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
}
.form-group input {
  width: calc(100% - 22px); /* Adjust for padding and border */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.error-message {
  color: red;
  margin-bottom: 10px;
}
.btn {
  padding: 10px 15px;
  text-decoration: none;
  border-radius: 5px;
  border: none;
  cursor: pointer;
  margin-right: 10px;
}
.btn-success {
  background-color: #28a745;
  color: white;
}
.btn-link {
  background-color: transparent;
  color: #007bff;
  text-decoration: underline;
}
</style>
