<template>
  <div data-testid="campaignDetails">
    <h3>Campaign Details</h3>
    <div v-if="error">{{error}}</div>
    <span>For version {{ currentCampaign.version }}(occurrence {{ currentCampaign.occurrence }})</span>
    <div>
      <label>Description</label>
      <div v-if="!isEditingDescription" @click="isEditingDescription =  true" class="description bordered">
        <div v-if="editableDescription" v-html="renderedMarkdown"/>
        <div v-else>There is no description. Please insert.</div>
      </div>
      <div v-else>
        <textarea
            class="description"
            v-model="editableDescription"
            placeholder="Write your description in markdown"/>
        <div>
          <BaseButton variant="update" @click="saveDescription">Save</BaseButton>
          <BaseButton variant="cancel" @click="cancelEditDescription">Cancel</BaseButton>
        </div>
      </div>
    </div>
    <div>
      <label>Status</label><span>(auto-saved)</span>
      <select
          v-model="selectedStatus"
          class="border p-1 rounded"
          @change="onStatusChange"
      >
        <option
            v-for="opt in nextStatuses.data"
            :key="opt"
            :value="opt"
        >
          {{ opt }}
        </option>
      </select>
    </div>
    <label>Tickets</label>
    <TicketScenarios
        v-for="(ticket, index) in currentCampaign.tickets"
        :key="ticket.id || index"
        :ticket="ticket"
        :occurrence="currentCampaign.occurrence"
        :version="currentCampaign.version"
        :project-name="currentCampaign.project_name"
        :data-testid="'ticketScenario-' + index"
    />
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {storeToRefs} from 'pinia'
import {useCampaignStore} from '@/stores/campaignStore'
import {campaignNextStatuses} from '@/services/campaignService'
import MarkdownIt from 'markdown-it'
import BaseButton from "@/components/utils/BaseButton.vue";
import {logger} from "@/composables/logger";
import TicketScenarios from "@/components/tickets/TicketScenarios.vue";

// --- Markdown renderer ---
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

// --- store references ---
const campaignStore = useCampaignStore();
const {projectName, version, occurrence, currentCampaign} = storeToRefs(campaignStore);
// -- Local references --
const isEditingDescription = ref(false);
const editableDescription = ref<string>("");
const nextStatuses = ref<{data: string[]}>({data: []});
const selectedStatus = ref<string>('');
const renderedMarkdown = computed(() => md.render(editableDescription.value));
const error = ref<string| null>(null);

// --- Fetch available statuses
onMounted(async () => {
  editableDescription.value = currentCampaign.value.description || "";
  selectedStatus.value = currentCampaign.value.status || "";
  nextStatuses.value = await campaignNextStatuses(currentCampaign.value.project_name, currentCampaign.value.status);
  nextStatuses.value.data.push(currentCampaign.value.status);
});

// --- Actions ---

async function saveDescription() {
  // Call to store to update the
  try {
    error.value = "";
    await campaignStore.updateCampaignOccurrenceDescription(editableDescription.value);
    isEditingDescription.value = false;
  }catch (e) {
    error.value = e.message;
  }
}

function cancelEditDescription() {
  editableDescription.value = currentCampaign.value.description;
  isEditingDescription.value = false;
}

async function onStatusChange(){
  try {
    error.value = "";
    await campaignStore.updateCampaignOccurrenceStatus(selectedStatus.value);
  }catch (e: any) {
    error.value = e.message;
  }
}
</script>


<style scoped>
.description {
  min-height: 150px;
  min-width: 200px;
}

.bordered {
  border: 1px solid rgba(0, 0, 0, 0.35);
}
</style>