<template>
  <div class="project-container">
    <h1>{{ projectName }}</h1>
    <div class="tabs">
      <button :class="{ active: activeTab === 'Version' }" @click="activeTab = 'Version'">Version
      </button>
      <button :class="{ active: activeTab === 'Campaigns' }" @click="activeTab = 'Campaigns'">
        Campaigns
      </button>
      <button :class="{ active: activeTab === 'Repository' }" @click="activeTab = 'Repository'">
        Repository
      </button>
      <button :class="{ active: activeTab === 'Bugs' }" @click="activeTab = 'Bugs'">Bugs</button>
    </div>
    <div class="tab-content">
      <component :is="currentTabComponent" :projectName="projectName"/>
    </div>
  </div>
</template>

<script>
import {ref, computed} from "vue";
import {useRoute} from "vue-router";
import VersionTab from "./versions/VersionTab.vue";

// Dummy placeholders for tabs not yet implemented.
const CampaignsTab = {
  template: "<div><h2>Campaigns</h2><p>Under Construction</p></div>",
};
const RepositoryTab = {
  template: "<div><h2>Repository</h2><p>Under Construction</p></div>",
};
const BugsTab = {
  template: "<div><h2>Bugs</h2><p>Under Construction</p></div>",
};

export default {
  name: "Project",
  components: {
    VersionTab,
  },
  setup() {
    const route = useRoute(); // Access route parameters
    const activeTab = ref("Version"); // Default tab

    // Compute project name from route params
    const projectName = computed(() => route.params.projectName);

    // Compute the currently active tab component
    const currentTabComponent = computed(() => {
      switch (activeTab.value) {
        case "Version":
          return VersionTab;
        case "Campaigns":
          return CampaignsTab;
        case "Repository":
          return RepositoryTab;
        case "Bugs":
          return BugsTab;
        default:
          return VersionTab;
      }
    });

    return {
      activeTab,
      projectName,
      currentTabComponent,
    };
  },
};
</script>

<style scoped>
.project-container {
  padding: 20px;
}

.tabs {
  margin-bottom: 20px;
}

.tabs button {
  padding: 10px;
  margin-right: 10px;
  border: none;
  background: #ddd;
  cursor: pointer;
}

.tabs button.active {
  background: #bbb;
  font-weight: bold;
}

.tab-content {
  border: 1px solid #ccc;
  padding: 20px;
}
</style>
