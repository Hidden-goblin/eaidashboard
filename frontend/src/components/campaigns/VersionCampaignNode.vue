<script setup lang="ts">
import {ref, computed} from 'vue';
import VersionCampaignOccurrenceLeaf from "@/components/campaigns/VersionCampaignOccurrenceLeaf.vue";
import {storeToRefs} from 'pinia';
import {useCampaignStore} from "@/stores/campaignStore";
import BaseButton from "@/components/utils/BaseButton.vue";

const campaignStore = useCampaignStore();
const {versionOccurrences, version} = storeToRefs(campaignStore);

const props = defineProps({
  version: {
    type: String,
    required: true
  },
  status: {
    type: String,
    required: true
  }
});
// Expansion control

const isExpanded = computed(() => version.value === props.version);
function toggle() {
  campaignStore.selectVersion(props.version);

}

function addOccurrence(){
  console.log("Occurrence added");
  campaignStore.createNewOccurrence(props.version);
}

</script>

<template>
  <div class="version-card">
    <div class="header" @click="toggle">
      <span>{{ props.version }}</span>
      <span class="status">({{ props.status }})</span>
      <button class="toggle-btn">{{ isExpanded ? "−" : "+" }}</button>
    </div>

    <div v-if="isExpanded" class="details">
      <BaseButton variant="create" @click.stop="addOccurrence">New Occurrence</BaseButton>
      <ul>
        <VersionCampaignOccurrenceLeaf
            v-for="occ in versionOccurrences(props.version)"
            :occurrenceStatus="occ.status"
            :occurrenceId="occ.occurrence"
            :version="props.version"
        />
      </ul>
    </div>
  </div>
</template>

<style scoped>
.version-card {
  border: 1px solid #ccc;
  border-radius: 6px;
  margin: 0.5pt 0;
  padding: 0.5rem;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-weight: bold;
}
.status {
  font-size: 0.8rem;
  color: #888;
}
.toggle-btn {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1.2rem;
}
.details {
  margin-top: 0.5rem;
  display: flex;
  flex-direction: column; /* stack vertically */
  gap: 0.5rem;              /* spacing between nodes */
  padding: 0.5rem;
}
.new-occ-btn {
  background: #e0e0e0;
  border: none;
  padding: 0.2rem 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  border-radius: 4px;
}
</style>