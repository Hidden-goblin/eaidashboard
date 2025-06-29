<!-- src/components/VersionTab.vue -->
<template>
  <div class="version-tab">
    <div class="header">
      <h2>Versions</h2>
      <div class="actions">
        <select v-model="selectedType" :class="styles.btnBase" @change="filterVersions">
          <option value="current">Current</option>
          <option value="future">Future</option>
          <option value="archived">Archived</option>
        </select>
        <BaseButton variant="create" @click="toggleNewVersionForm">Create New Version</BaseButton>
      </div>
    </div>

    <CreateVersionForm
        v-if="showNewVersionForm"
        :projectName="projectName"
        @version-created="handleVersionCreated"
        @close="toggleNewVersionForm"
    />

    <UpdateVersionForm
        v-if="showUpdateVersionForm"
        :projectName="projectName"
        :activeVersionId="updateVersionId"
        @version-updated="handleVersionUpdated"
        @close="toggleUpdateVersionForm"
    />

    <div v-if="loading" class="loading">Loading versions...</div>

    <div v-else>
      <p v-if="displayedVersions.length === 0">No versions found.</p>
      <div class="version-list">
        <VersionCard
            v-for="version in displayedVersions"
            :key="version.version"
            :version="version"
            :isActive="activeVersionId === version.version"
            @toggle-tickets="toggleTickets"
            @toggle-update="toggleUpdateVersionForm"
        />
      </div>
    </div>

    <VersionTickets
        v-if="activeVersionId"
        :projectName="projectName"
        :versionId="activeVersionId"
        @close="() => (activeVersionId = null)"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useVersionStore } from '../../stores/versionStore'
import CreateVersionForm from './CreateVersionForm.vue'
import UpdateVersionForm from './UpdateVersionForm.vue'
import VersionTickets from './VersionTickets.vue'
import VersionCard from './VersionCard.vue'
import styles from '../../styles/buttons.module.css'
import BaseButton from "../utils/BaseButton.vue";

// Props
const props = defineProps({
  projectName: {
    type: String,
    required: true
  }
})

// Stores
const versionStore = useVersionStore()
const { selectedType, displayedVersions, loading } = storeToRefs(versionStore)

// Local State
const showNewVersionForm = ref(false)
const showUpdateVersionForm = ref(false)
const activeVersionId = ref(null)
const updateVersionId = ref(null)

// Watchers
watch(() => selectedType.value, () => {
  versionStore.fetchVersions()
}, { immediate: true })

watch(() => props.projectName, () => {
  versionStore.resetVersions()
  versionStore.fetchVersions()
}, { immediate: true })

onMounted(versionStore.fetchVersions)

// Methods
const toggleTickets = (versionId) => {
  activeVersionId.value = activeVersionId.value === versionId ? null : versionId
}

const toggleNewVersionForm = () => {
  showNewVersionForm.value = !showNewVersionForm.value
}

const toggleUpdateVersionForm = (versionId) => {
  updateVersionId.value = updateVersionId.value === versionId ? null : versionId
  showUpdateVersionForm.value = !showUpdateVersionForm.value
}

const handleVersionCreated = (newVersion) => {
  versionStore.addVersion(newVersion)
  showNewVersionForm.value = false
}

const handleVersionUpdated = () => {
  versionStore.resetVersions()
  showUpdateVersionForm.value = false
  updateVersionId.value = null
  versionStore.fetchVersions()
}

// Optional: dummy function for filter trigger (select @change)
const filterVersions = () => {
  versionStore.fetchVersions()
}
</script>

<style scoped>
.version-tab {
  padding: 10px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.version-list {
  list-style: none;
  padding: 0;
  margin-top: 15px;
}

button {
  padding: 5px 10px;
  margin: 0 5px;
  border: none;
  background: #007bff;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

.loading {
  font-style: italic;
}
</style>
