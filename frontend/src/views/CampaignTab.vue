<script setup lang="ts">
import CampaignsAccess  from "@/components/campaigns/CampaignsAccess.vue";
import CampaignDetails from "@/components/campaigns/CampaignDetails.vue";

const props = defineProps({
  projectName: {
    type: String,
    required: true
  }
})

</script>

<template>
  <div class="container">
    <CampaignsAccess :projectName="projectName"
                     class="access" ></CampaignsAccess>

    <CampaignDetails class="details"
                     ></CampaignDetails>
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