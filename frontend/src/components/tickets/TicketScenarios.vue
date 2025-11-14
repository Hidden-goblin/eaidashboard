<script setup lang="ts">
import type {components} from "@/api/openapi";
import ScenarioExecution from "@/components/scenarios/ScenarioExecution.vue";

type TicketScenario = components.schemas.TicketScenario;

const {projectName, version, occurrence, ticket} = defineProps<{
  projectName: string
  version: string
  occurrence: string
  ticket: TicketScenario
}>()
</script>

<template>
  <div>{{ ticket.reference }} - {{ ticket.summary }}</div>
  <b>Scenarios</b>
  <ScenarioExecution v-for="sc in ticket.scenarios"
                     :projectName="projectName"
                     :version="version"
                     :occurrence="occurrence"
                     :scenario="sc"
                     :data-testid="'scenarioFor-'+ticket.reference+'-'+sc.scenario_tech_id"/>
  <pre>{{ ticket }}</pre>
</template>

<style scoped>

</style>