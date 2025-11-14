<script setup lang="ts">
import BaseButton from "@/components/utils/BaseButton.vue";
import  {useCampaignStore} from "@/stores/campaignStore";

const campaignStore = useCampaignStore();

const props = defineProps({
  version: {
    type: String,
    required: true
  },
  occurrenceStatus: {
    type: String,
    required: true
  },
  occurrenceId: {
    type: Number,
    required:true
  }
});

function showDetail(){
  console.log("show details "+ props.version + " " + props.occurrenceId);
  campaignStore.selectOccurrence(props.occurrenceId);
}

</script>

<template>
  <div class="occurrence-leaf">
    <div>
      <strong>Occurrence {{props.occurrenceId}}</strong>
    </div>
    <div>
      {{props.occurrenceStatus}}
    </div>
    <div>
      <BaseButton iconOnly variant="view" @click="showDetail"/>
    </div>
  </div>
</template>

<style scoped>
.occurrence-leaf{
  margin-top: 0.5rem;
  display: flex;
  flex-direction: row; /* stack vertically */
  gap: 0.5rem;              /* spacing between nodes */
  padding: 0.5rem;
}
</style>