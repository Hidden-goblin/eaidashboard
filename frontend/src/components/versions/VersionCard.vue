<!-- src/components/VersionCard.vue -->
<template>
  <div class="version-card">
    <div class="info">
      <strong>{{ version.version }}</strong> ({{ version.status }}) Start date {{ formatDate(version.started) }} - end
      forecast {{ formatDate(version.end_forecast) }}
    </div>
    <div class="actions">
      <BaseButton variant="view" @click="$emit('toggle-tickets', version.version)">
        {{ isActive ? 'Hide Tickets' : 'Show Tickets' }}
      </BaseButton>
      <BaseButton variant="update" @click="$emit('toggle-update', version.version)">Update</BaseButton>
    </div>
  </div>
</template>

<script setup>

import BaseButton from "@/components/utils/BaseButton.vue";

defineProps({
  version: {type: Object, required: true},
  isActive: {type: Boolean, default: false}
});

const formatDate = (dateStr) => {
  if (!dateStr || dateStr === null) return 'N/A';
  return dateStr.split('T')[0]; // YYYY-MM-DD
};
</script>

<style scoped>
.version-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9f9f9;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 10px;
}

.actions button {
  margin-left: 10px;
}
</style>
  