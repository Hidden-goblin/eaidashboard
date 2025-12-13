<template>
  <nav class="navbar">
    <!-- Brand & burger -->
    <div class="navbar-left">

      <button class="burger" @click="toggleMenu" aria-label="Toggle menu">☰</button>
    </div>

    <!-- Right-side Login/Logout buttons -->
    <div class="navbar-right">
      <template v-if="!authStore.isAuthenticated">
        <BaseButton @click="showLoginModal = true" :icon="ArrowRightEndOnRectangleIcon">Login</BaseButton>
      </template>
      <template v-else>
        <BaseButton :icon="ArrowRightStartOnRectangleIcon" @click="handleLogout">Logout</BaseButton>
      </template>
    </div>

    <!-- Side menu -->
    <div class="side-menu" :class="{ open: isMenuOpen }">
      <BaseButton to="/" class="navbar-brand">Dashboard</BaseButton>
      <div v-if="authStore.isAuthenticated && authStore.allProjects.length > 0" class="project-selector">
        <select v-model="selectedProject" @change="goToProject" :class="styles.btnBase">
          <option disabled value="">Select a project</option>
          <option
              v-for="project in authStore.filteredProjects"
              :key="project"
              :value="project"
          >
            {{ project }}
          </option>
        </select>
        <BaseButton
            variant="navigate"
            :disabled="!selectedProject"
            @click="goToProject"
        >Go to project
        </BaseButton>

        <BaseButton
            v-if="authStore.isSuperAdmin"
            @click="goToAdmin"
            variant="admin"
        >Administration
        </BaseButton>
      </div>
    </div>

    <!-- Login Modal -->
    <LoginModal
        v-if="showLoginModal"
        @login-success="handleLogin"
        @close="showLoginModal = false"
    />
  </nav>
</template>
<script setup>
import {ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import {storeToRefs} from 'pinia';

import {useAuthStore} from '../stores/authStore.ts';
import {useVersionStore} from '../stores/versionStore.ts';
import LoginModal from './access/LoginModal.vue';
import BaseButton from "./utils/BaseButton.vue";
import {ArrowRightStartOnRectangleIcon, ArrowRightEndOnRectangleIcon} from '@heroicons/vue/20/solid';
import styles from '../styles/buttons.module.css';

// Stores
const authStore = useAuthStore();
const versionStore = useVersionStore();

// Router
const router = useRouter();

// State
const isMenuOpen = ref(false);
const {showLoginModal} = storeToRefs(authStore);
const {selectedProject} = storeToRefs(versionStore);

// Methods
const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
};

const goToProject = () => {
  toggleMenu();
  if (selectedProject.value) {
    router.push(`/projects/${selectedProject.value}`);
  }
};

const goToAdmin = () => {
  router.push('/admin');
};

const handleLogin = () => {
  authStore.fetchProjects();
  showLoginModal.value = false;
};

const handleLogout = () => {
  authStore.logout();
  router.push('/');
};

watch(selectedProject, (newProject) => {
  if (newProject) {
    router.push(`/projects/${newProject}`);
  }
});
</script>
<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #eee;
  padding: 10px;
  position: relative;
}

/* Left section with brand and burger */
.navbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Burger button */
.burger {
  font-size: 24px;
  background: none;
  border: none;
  cursor: pointer;
}

/* Right side (Login/Logout) */
.navbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Side menu styling */
.side-menu {
  position: absolute;
  top: 100%;
  left: 10px;
  background: white;
  border: 1px solid #ccc;
  padding: 15px;
  display: none;
  flex-direction: column;
  z-index: 1000;
}

.side-menu.open {
  display: flex;
}

.project-selector {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
