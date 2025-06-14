<template>
  <div class="project-bugs-view">
    <h4>Bugs</h4>

    <div class="actions">
      <button @click="openCreateBugModal" class="btn btn-sm btn-primary">Report New Bug</button>
    </div>

    <!-- Filtering options -->
    <div class="filters form-inline">
      <div class="form-group">
        <label for="versionFilter">Version:</label>
        <select id="versionFilter" v-model="selectedVersionFilter" @change="applyFilters" class="form-control input-sm">
          <option value="">All Versions</option>
          <option v-for="version in projectStore.currentProject?.versions" :key="version.id || version.version" :value="version.version">
            {{ version.version }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="statusFilterBug">Status:</label>
        <select id="statusFilterBug" v-model="selectedStatusFilter" @change="applyFilters" class="form-control input-sm">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="fix_ready">Fix Ready</option>
          <option value="closed">Closed</option>
          <!-- Add more statuses as defined -->
        </select>
      </div>
    </div>

    <!-- Create/Edit Bug Modal -->
    <div v-if="showBugModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeBugModal">&times;</span>
        <h5>{{ editingBug ? 'Edit Bug' : 'Report New Bug' }}</h5>
        <form @submit.prevent="handleSaveBug">
          <div class="form-group">
            <label for="bugTitle">Title:</label>
            <input type="text" id="bugTitle" v-model="currentBug.title" required />
          </div>
          <div class="form-group">
            <label for="bugDescription">Description:</label>
            <textarea id="bugDescription" v-model="currentBug.description"></textarea>
          </div>
          <div class="form-group">
            <label for="bugVersion">Reported in Version:</label>
            <select id="bugVersion" v-model="currentBug.version" required>
              <option disabled value="">Select version</option>
              <option v-for="version in projectStore.currentProject?.versions" :key="version.id || version.version" :value="version.version">
                {{ version.version }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="bugCriticality">Criticality:</label>
            <select id="bugCriticality" v-model="currentBug.criticality">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div class="form-group">
            <label for="bugStatusModal">Status:</label> <!-- Renamed to avoid conflict with filter id -->
            <select id="bugStatusModal" v-model="currentBug.status">
              <option value="open">Open</option>
              <option value="fix_ready">Fix Ready</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div v-if="projectStore.bugsError" class="error-message">{{ projectStore.bugsError }}</div>
          <button type="submit" :disabled="projectStore.isBugsLoading" class="btn btn-success btn-sm">
            {{ projectStore.isBugsLoading ? 'Saving...' : 'Save Bug' }}
          </button>
          <button type="button" @click="closeBugModal" class="btn btn-link btn-sm">Cancel</button>
        </form>
      </div>
    </div>

    <div v-if="projectStore.isBugsLoading && projectStore.projectBugs.length === 0" class="loading">Loading bugs...</div>
    <div v-if="projectStore.bugsError && !showBugModal" class="error-message">{{ projectStore.bugsError }}</div>

    <table v-if="projectStore.projectBugs.length > 0" class="bugs-table">
      <thead>
        <tr>
          <th>Title</th>
          <th>Version</th>
          <th>Criticality</th>
          <th>Status</th>
          <th>Reported At</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="bug in projectStore.projectBugs" :key="bug.id">
          <td>{{ bug.title }}</td>
          <td>{{ bug.version }}</td>
          <td>{{ bug.criticality }}</td>
          <td>{{ bug.status }}</td>
          <td>{{ formatDate(bug.created_at || bug.reported_at) }}</td>
          <td>
            <button @click="openEditBugModal(bug)" class="btn btn-xs btn-info">Edit</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!projectStore.isBugsLoading && projectStore.projectBugs.length === 0 && !projectStore.bugsError" class="no-data">
      No bugs found for the current filters.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue';
import { useProjectStore } from '../../stores/projectStore';
import { useRoute } from 'vue-router';

const projectStore = useProjectStore();
const route = useRoute();
const projectId = computed(() => route.params.id);

const showBugModal = ref(false);
const editingBug = ref(null);
const currentBug = reactive({
  id: null, title: '', description: '', version: '',
  criticality: 'medium', status: 'open'
});
const selectedVersionFilter = ref('');
const selectedStatusFilter = ref('');


const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const resetCurrentBug = () => {
  currentBug.id = null; currentBug.title = ''; currentBug.description = '';
  // Default to first available version or an empty string if no versions.
  currentBug.version = projectStore.currentProject?.versions?.[0]?.version || '';
  currentBug.criticality = 'medium'; currentBug.status = 'open';
  projectStore.bugsError = null; // Clear any previous error
};

const openCreateBugModal = () => {
  resetCurrentBug();
  editingBug.value = null;
  showBugModal.value = true;
};

const openEditBugModal = (bug) => {
  editingBug.value = bug;
  // Assign all properties from bug to currentBug
  Object.assign(currentBug, bug);
  projectStore.bugsError = null;
  showBugModal.value = true;
};

const closeBugModal = () => {
  showBugModal.value = false;
  editingBug.value = null;
  resetCurrentBug(); // Resets form and clears errors
};

const handleSaveBug = async () => {
  // Create a shallow copy for submission, exclude 'id' if it's a new bug
  const bugData = { ...currentBug };
  if (!editingBug.value) {
    delete bugData.id;
  }

  try {
    if (editingBug.value) {
      await projectStore.updateBug(projectId.value, editingBug.value.id, bugData);
    } else {
      await projectStore.createBug(projectId.value, bugData);
    }
    closeBugModal();
    applyFilters(); // Refresh list
  } catch (e) {
    // Error is expected to be set in the store and displayed in the modal.
  }
};

const applyFilters = () => {
    const filters = {};
    if(selectedVersionFilter.value) filters.version = selectedVersionFilter.value;
    if(selectedStatusFilter.value) filters.status = selectedStatusFilter.value;
    projectStore.fetchBugsForProject(projectId.value, filters);
}

const ensureProjectDataAndLoadBugs = async () => {
  if (!projectId.value) return;
  // Ensure current project details (especially versions for filter) are loaded
  if (!projectStore.currentProject || projectStore.currentProject.id !== projectId.value) {
    await projectStore.fetchProjectDetails(projectId.value);
  }

  // If versions are not part of project details OR not yet loaded for current project
  if (projectStore.currentProject && (!projectStore.currentProject.versions || projectStore.currentProject.versions.length === 0)) {
    // Only fetch if not already loading to prevent races
    if (!projectStore.isVersionsLoading) {
      await projectStore.fetchProjectVersions(projectId.value);
    }
  }

  // Set default version for new bug form if versions are now available
  if (!currentBug.version && projectStore.currentProject?.versions?.length > 0) {
      currentBug.version = projectStore.currentProject.versions[0].version;
  }
  applyFilters(); // Load bugs with current filters
};


onMounted(() => {
  ensureProjectDataAndLoadBugs();
});

watch(() => projectId.value, (newId, oldId) => {
    if (newId && newId !== oldId) {
        ensureProjectDataAndLoadBugs();
    }
});

// If versions list could change after initial load (e.g. new version created in another tab)
// this watcher can help keep the filter list up-to-date.
watch(() => projectStore.currentProject?.versions, (newVersions) => {
    if (!currentBug.version && newVersions?.length > 0) {
        currentBug.version = newVersions[0].version;
    }
    // Check if selectedVersionFilter is still valid
    if (selectedVersionFilter.value && !newVersions?.find(v => v.version === selectedVersionFilter.value)) {
        selectedVersionFilter.value = ""; // Reset if selected version no longer exists
        applyFilters(); // Re-apply filters if version filter was reset
    }
}, { deep: true });


</script>

<style scoped>
.project-bugs-view { padding-top: 15px; }
.actions, .filters { margin-bottom: 15px; }
.filters.form-inline .form-group { margin-right: 15px; }
.filters label { margin-right: 5px; font-weight: normal; }
.filters select.input-sm { height: 30px; padding: 5px 10px; font-size: 12px; line-height: 1.5; }

.modal {
  position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
  overflow: auto; background-color: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
}
.modal-content {
  background-color: #fefefe; padding: 20px; border: 1px solid #888;
  width: 80%; max-width: 600px; border-radius: 8px; position: relative;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.close {
  color: #aaa; position: absolute; top: 10px; right: 15px;
  font-size: 28px; font-weight: bold; cursor: pointer;
}
.close:hover, .close:focus { color: black; text-decoration: none; }

.form-group { margin-bottom: 10px; }
.form-group label { display: block; margin-bottom: 5px; font-size: 0.9em; font-weight: bold;}
.form-group input, .form-group textarea, .form-group select {
  width: calc(100% - 22px); /* Full width minus padding/border */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group textarea { min-height: 80px; resize: vertical; }

.bugs-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
.bugs-table th, .bugs-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
.bugs-table th { background-color: #f0f0f0; font-weight: bold; }

.loading, .error-message, .no-data { text-align: center; padding: 20px; font-size: 1.1em; }
.error-message { color: #d9534f; margin-bottom: 10px; }
.no-data { color: #777; }

.btn-sm { padding: 8px 12px; font-size: 0.9em; }
.btn-xs { padding: 4px 8px; font-size: 0.8em; }
.btn-link { background-color: transparent; color: #007bff; text-decoration: underline; border: none; }
</style>
