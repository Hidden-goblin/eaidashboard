<script setup lang="ts">
import type {components} from "@/api/openapi";
type ScenarioExecutionType = components.schemas.ScenarioExecution;

const {projectName, version, occurrence, scenario} = defineProps<{
  projectName: string
  version: string
  occurrence: number
  scenario: ScenarioExecutionType
}>()
</script>

<template>
  <div>
    <b>{{scenario.reference}}</b> {{scenario.name}} ({{scenario.epic}}>{{scenario.feature_name}})
    <b>{{scenario.status}}</b>
    <pre>{{scenario.steps}}</pre>
  </div>
</template>

<style scoped>

</style>