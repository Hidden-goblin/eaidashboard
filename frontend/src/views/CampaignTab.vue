<script setup lang="ts">
import CampaignsAccess  from "@/components/campaigns/CampaignsAccess.vue";
import CampaignDetails from "@/components/campaigns/CampaignDetails.vue";
const props = defineProps({
  projectName: {
    type: String,
    required: true
  }
})
const version = ref<string | null>(null);
const occurrence = ref<number | null>(null);

function onVersionOccurrenceSelected(versionOccurrence: Object){
  version.value = versionOccurrence.version;
  occurrence.value = versionOccurrence.occurrence
}

</script>

<template>
  <div class="container">
    <CampaignsAccess :project-name="projectName"
                     class="access"
                     @selectVersionOccurrence="onVersionOccurrenceSelected" ></CampaignsAccess>

    <CampaignDetails class="details"
                     :project-name="projectName"
                     :version="version"
                     :occurrence="occurrence"></CampaignDetails>
  </div>
</template>

<style scoped>
.container {
  display: flex;
  gap: 1rem; /* space between the components */
}

.access {
  flex: 0 0 30%; /* fixed at 30% width */
}

.details {
  flex: 1; /* takes the remaining space (70%) */
}
</style>