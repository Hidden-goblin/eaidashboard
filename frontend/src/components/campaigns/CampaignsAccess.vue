<script setup lang="ts">
import {getProjectDetails} from "@/services/campaignService";
const props = defineProps({
  projectName: {
    type: String,
    required: true
  }
})

const emit = defineEmits<{
  (e: "selectVersionOccurrence", versionOccurrence: Object): void;
}>();

function chooseVersionOccurrence(versionOccurrence: object) {
  emit("selectVersionOccurrence", versionOccurrence);
}


</script>

<template>
<div>
  <h1>This is my tree view</h1>
</div>
</template>

<style scoped>

</style>