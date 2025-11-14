<template>
  <div class="campaign-occurrence-view">
    <div v-if="loading" class="loading">Loading campaign details...</div>

    <div v-else-if="error" class="error">
      ⚠️ {{ error }}
    </div>

    <VersionCampaignOccurrenceDetails v-else-if="currentCampaign"/>

    <div v-else>
      <p>Select a version and occurrence to view details.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, watch} from 'vue'
import {storeToRefs} from 'pinia'
import {useCampaignStore} from '@/stores/campaignStore'
import VersionCampaignOccurrenceDetails from "@/components/campaigns/VersionCampaignOccurrenceDetails.vue";

// --- store references ---
const campaignStore = useCampaignStore();
const {projectName, version, occurrence, currentCampaign} = storeToRefs(campaignStore)

// --- local state ---
const loading = ref(false)
const error = ref<string | null>(null)

// --- reactive watcher ---
watch(
    [version, occurrence],
    async ([newVersion, newOccurrence]) => {
      if (!newVersion || newOccurrence === null) {
        currentCampaign.value = null
        return
      }

      try {
        loading.value = true
        error.value = null
        await campaignStore.retrieveCampaignOccurrence(projectName.value,
            newVersion,
            newOccurrence)
      } catch (err: any) {
        console.error(err)
        error.value = err.message ?? 'Failed to load campaign data'
      } finally {
        loading.value = false
      }
    },
    {immediate: true}
)
</script>

<style scoped>
.campaign-occurrence-view {
  padding: 1rem;
}

.loading {
  color: #666;
}

.error {
  color: red;
  font-weight: bold;
}
</style>