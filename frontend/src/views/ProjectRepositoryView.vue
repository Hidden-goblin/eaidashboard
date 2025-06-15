<template>
  <div class="project-repository-view">
    <h4>Test Repository</h4>

    <!-- CSV Import Section -->
    <div class="import-section card">
      <h5>Import Scenarios from CSV</h5>
      <form @submit.prevent="handleCsvImport">
        <div class="form-group">
          <label for="csvFile">Select CSV File:</label>
          <input type="file" id="csvFile" @change="onFileSelected" accept=".csv" required />
        </div>
        <button type="submit" :disabled="projectStore.isRepositoryLoading || !selectedFile" class="btn btn-sm btn-success">
          {{ projectStore.isRepositoryLoading && isImporting ? 'Importing...' : 'Import CSV' }}
        </button>
        <div v-if="importError" class="error-message import-error">{{ importError }}</div>
        <div v-if="projectStore.repositoryError && !importError" class="error-message import-error">
          General Error: {{ projectStore.repositoryError }}
        </div>
      </form>
    </div>

    <!-- Repository Browser Section -->
    <div class="browser-section card">
      <h5>Browse Repository</h5>
      <div class="filters-row">
        <div class="form-group">
          <label for="epicSelector">Epic:</label>
          <select id="epicSelector" v-model="selectedEpicId" @change="onEpicSelected" :disabled="projectStore.isRepositoryLoading">
            <option value="">Select Epic</option>
            <option v-for="epic in projectStore.projectRepositoryEpics" :key="epic.id" :value="epic.id">
              {{ epic.name }} ({{ epic.id }})
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="featureSelector">Feature:</label>
          <select id="featureSelector" v-model="selectedFeatureId" @change="onFeatureSelected" :disabled="!selectedEpicId || projectStore.isRepositoryLoading">
            <option value="">Select Feature</option>
            <option v-for="feature in projectStore.projectRepositoryFeatures" :key="feature.id" :value="feature.id">
              {{ feature.name }} ({{ feature.id }})
            </option>
          </select>
        </div>
      </div>

      <div v-if="projectStore.isRepositoryLoading && projectStore.projectRepositoryScenarios.length === 0 && !isImporting" class="loading">Loading scenarios...</div>
      <div v-if="projectStore.repositoryError && !importError" class="error-message">{{ projectStore.repositoryError }}</div>

      <table v-if="projectStore.projectRepositoryScenarios.length > 0" class="scenarios-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name / Description</th>
            <th>Status</th>
            <th>Feature ID</th>
            <!-- Add other relevant scenario fields -->
          </tr>
        </thead>
        <tbody>
          <tr v-for="scenario in projectStore.projectRepositoryScenarios" :key="scenario.id">
            <td>{{ scenario.id }}</td>
            <td>{{ scenario.name || scenario.description }}</td>
            <td>{{ scenario.status || 'N/A' }}</td>
            <td>{{ scenario.feature_id }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!projectStore.isRepositoryLoading && selectedFeatureId && projectStore.projectRepositoryScenarios.length === 0 && !projectStore.repositoryError" class="no-data">
        No scenarios found for the selected feature.
      </div>
      <div v-if="!selectedFeatureId && !projectStore.isRepositoryLoading" class="no-data">
        Select an Epic and Feature to view scenarios.
      </div>
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

const selectedFile = ref(null);
const importError = ref(null);
const isImporting = ref(false); // Specific loading state for import

const selectedEpicId = ref('');
const selectedFeatureId = ref('');

const onFileSelected = (event) => {
  selectedFile.value = event.target.files[0];
  projectStore.repositoryError = null;
  importError.value = null;
};

const handleCsvImport = async () => {
  if (!selectedFile.value) {
    importError.value = "Please select a file to import.";
    return;
  }
  importError.value = null;
  projectStore.repositoryError = null; // Clear general repo error before import attempt
  isImporting.value = true;
  try {
    await projectStore.importRepositoryCsv(projectId.value, selectedFile.value);
    alert('CSV imported successfully! Epics list will be refreshed.');
    selectedFile.value = null;
    const fileInput = document.getElementById('csvFile');
    if(fileInput) fileInput.value = null;
    // Epics are refetched in store, this will trigger watchers if necessary.
    // Reset selections to reflect new data state
    selectedEpicId.value = '';
    selectedFeatureId.value = '';
    projectStore.projectRepositoryFeatures = [];
    projectStore.projectRepositoryScenarios = [];

  } catch (e) {
    // Error is set in projectStore.repositoryError by the action if it's a general API error
    // Or specific handling if needed:
    importError.value = e.message || "CSV import failed.";
    console.error("Import error:", e);
  } finally {
    isImporting.value = false;
  }
};

const onEpicSelected = async () => {
  selectedFeatureId.value = '';
  projectStore.projectRepositoryScenarios = [];
  if (selectedEpicId.value) {
    await projectStore.fetchFeatures(projectId.value, selectedEpicId.value);
  } else {
    projectStore.projectRepositoryFeatures = [];
  }
};

const onFeatureSelected = async () => {
  if (selectedFeatureId.value && selectedEpicId.value) {
    await projectStore.fetchScenarios(projectId.value, selectedEpicId.value, selectedFeatureId.value);
  } else {
    projectStore.projectRepositoryScenarios = [];
  }
};

const loadInitialData = () => {
    if (projectId.value) {
        projectStore.fetchEpics(projectId.value);
    }
    // Reset selections and dependent data
    selectedEpicId.value = '';
    selectedFeatureId.value = '';
    projectStore.projectRepositoryFeatures = [];
    projectStore.projectRepositoryScenarios = [];
    importError.value = null; // Clear import error on mount/project change
};

onMounted(() => {
  loadInitialData();
});

watch(projectId, (newProjectId) => {
  if (newProjectId) {
    loadInitialData();
  }
});

// Watch for changes to epics list (e.g., after import) to potentially clear selections if needed
watch(() => projectStore.projectRepositoryEpics, () => {
    // If selected epic is no longer in the list, reset
    if (selectedEpicId.value && !projectStore.projectRepositoryEpics.find(e => e.id === selectedEpicId.value)) {
        selectedEpicId.value = '';
        selectedFeatureId.value = ''; // Also reset feature
        projectStore.projectRepositoryFeatures = [];
        projectStore.projectRepositoryScenarios = [];
    }
}, { deep: true });


</script>

<style scoped>
.project-repository-view { padding-top: 15px; }
.card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 20px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.card h5 { margin-top: 0; color: #333; font-size: 1.1em; margin-bottom: 15px;}
.import-section .form-group { margin-bottom: 10px; }
.import-section input[type="file"] { display: block; margin-top: 5px; padding: 5px; border: 1px solid #ccc; border-radius: 4px;}
.import-error { margin-top: 10px; color: red; font-size: 0.9em; }

.browser-section .filters-row { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
.browser-section .form-group { flex: 1; min-width: 200px; } /* Allow wrapping on smaller screens */
.browser-section .form-group label { display: block; margin-bottom: 5px; font-size: 0.9em; font-weight: bold; }
.browser-section .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }

.scenarios-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
.scenarios-table th, .scenarios-table td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 0.9em; }
.scenarios-table th { background-color: #f0f0f0; font-weight: bold; }

.loading, .no-data { text-align: center; padding: 20px; font-size: 1.1em; color: #777; }
.error-message { text-align: center; padding: 10px; color: #d9534f; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; margin-bottom: 15px;}
.btn-sm { padding: 8px 12px; font-size: 0.9em; }
</style>
