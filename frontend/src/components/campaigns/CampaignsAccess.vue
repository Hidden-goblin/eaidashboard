<script setup lang="ts">
import { onMounted, ref } from 'vue';
import {storeToRefs} from 'pinia';
import {useCampaignStore} from "@/stores/campaignStore";
import VersionCampaignNode from "@/components/campaigns/VersionCampaignNode.vue";
import BaseButton from "@/components/utils/BaseButton.vue";
import {logger} from "@/composables/logger";

const props = defineProps({
  projectName: {
    type: String,
    required: true
  }
})

const error = ref<string>("");
const campaignStore = useCampaignStore();
const { projectName, versions, isLoading } = storeToRefs(campaignStore);
onMounted(()=>{
  try {
    logger.debug("Run get campaign");
    error.value = "";
    projectName.value = props.projectName;
    campaignStore.getVersionCampaigns(true);
  } catch (e: any){
    error.value = e.message;
  }
})

function loadMore(){
    console.log("load more");
    campaignStore.getVersionCampaigns();
}

</script>

<template>
  <div class="version-list">
    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="!error">
    <VersionCampaignNode
        v-for="(v, index) in versions"
        :key="v.version + '-' + index"
        :data-testid="v.version + '-' + index"
        :version="v.version"
        :status="v.status"
    />
      <BaseButton v-if="campaignStore.hasMore()" variant="create" @click="loadMore">Load more</BaseButton>
    </div>    
  </div>
</template>

<style scoped>
.version-list {
  display: flex;
  flex-direction: column; /* stack vertically */
  gap: 2pt;              /* spacing between nodes */
  padding: 0.5rem;
}

</style>