<template>
  <div class="projectCard">
    <!-- Project name and version -->
    <div class="header">
      <span class="project-name"
            :data-testid="`project-name-${index}`">{{ projectName }}</span>
      <span class="project-version"
            :data-testid="`project-version-${index}`">Version {{ projectVersion }}</span>
    </div>

    <!-- Ticket status as a colored progress bar -->
    <div class="section">
      <h3>Ticket Status</h3>
      <div class="progress-bar">
        <div
            v-for="(value, status) in nonZeroTickets"
            :key="status"
            :class="['segment', status]"
            :style="{ width: getPercentage(value) + '%' }"
            :title="`${value} ticket${value > 1 ? 's' : ''}`"
            :data-testid="`ticket-${index}-${status}`"
        >
          <span class="label" v-if="getPercentage(value) > 8">{{ status }} ({{ value }})</span>
        </div>
      </div>
    </div>

    <div class="section bugs">
      <h3>Bugs</h3>
      <div class="bug-types-horizontal">
        <div class="bug-column" v-for="type in ['blocking', 'major', 'minor']" :key="type">
          <div class="bug-label">{{ type.charAt(0).toUpperCase() + type.slice(1) }}</div>
          <div class="bug-progress">
            <div
                class="bug-segment open"
                :style="{ width: getBugPercentage(type, 'open') + '%' }"
                :title="`${bugs['open_' + type]} open`"
                :data-testid="`bug-${index}-${type}-open`"
            />
            <div
                class="bug-segment closed"
                :style="{ width: getBugPercentage(type, 'closed') + '%' }"
                :title="`${bugs['closed_' + type]} closed`"
                :data-testid="`bug-${index}-${type}-closed`"
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import {computed} from 'vue';

const {projectName, projectVersion, tickets, bugs} = defineProps({
  projectName: String,
  projectVersion: String,
  tickets: Object,
  bugs: Object,
  index: Number
});

const nonZeroTickets = computed(() => {
  return Object.entries(tickets)
      .filter(([_, value]) => value > 0)
      .reduce((obj, [key, value]) => {
        obj[key] = value;
        return obj;
      }, {});
});
/**
 * Helper: return percentage based on sum of all ticket values
 */
const getPercentage = (value) => {
  const total = Object.values(tickets).reduce((sum, v) => sum + v, 0);
  if (total === 0) return 0
  return (value / total) * 100
}

const getBugPercentage = (type, state) => {
  const open = bugs[`open_${type}`] || 0;
  const closed = bugs[`closed_${type}`] || 0;
  const total = open + closed;
  if (total === 0) return 0;
  return ((state === 'open' ? open : closed) / total) * 100;
};
</script>

<style scoped>
.projectCard {
  background: #f4f4f4;
  border-radius: 10px;
  padding: 16px;
  font-family: sans-serif;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.432);
  max-width: 1000px;
  margin: 1rem auto;
}

.header {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}

.project-name {
  font-size: 1.5rem;
  font-weight: bold;
}

.project-version {
  font-size: 1.1rem;
  color: #666;
}

.section {
  margin-top: 1.5rem;
}

.progress-bar {
  display: flex;
  height: 28px;
  border-radius: 6px;
  overflow: hidden;
  background: #e0e0e0;
  font-size: 0.75rem;
}

.segment {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  white-space: nowrap;
  padding: 0 4px;
  transition: width 0.3s ease;
}

.segment.open {
  background-color: #3498db; /* blue */
}

.segment.in_progress {
  background-color: #f1c40f; /* yellow */
  color: black;
}

.segment.blocked {
  background-color: #e74c3c; /* red */
}

.segment.cancelled {
  background-color: #95a5a6; /* grey */
}

.segment.done {
  background-color: #2ecc71; /* green */
}

.bugs {
  margin-top: 1rem;
}

.bug-types-horizontal {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}

.bug-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bug-label {
  margin-bottom: 0.5rem;
  font-weight: bold;
  text-transform: capitalize;
}

.bug-progress {
  width: 100%;
  display: flex;
  height: 20px;
  border-radius: 4px;
  overflow: hidden;
  background: #ddd;
}

.bug-segment {
  height: 100%;
  transition: width 0.3s ease;
}

.bug-segment.open {
  background-color: #3498db;
}

.bug-segment.closed {
  background-color: #2ecc71;
}

</style>
  