<template>
    <nav class="navbar">
      <div class="navbar-brand"><a href="/"> Dashboard</a></div>
  
      <div class="navbar-menu">
        <!-- If not logged in, show login button -->
        <div v-if="!authStore.isAuthenticated">
          <button @click="showLoginModal = true">Login</button>
        </div>
  
        <!-- If logged in, show project selector and admin button -->
        <div v-else>
          <div class="project-selector" v-if="authStore.allProjects.length > 0">
            <select v-model="selectedProject" @change="goToProject">
              <option disabled value="">Select a project</option>
              <option
                v-for="project in authStore.filteredProjects"
                :key="project"
                :value="project"
              >
                {{ project }}
              </option>
            </select>
          </div>
          <div>
            <button v-if="authStore.isSuperAdmin" @click="goToAdmin">
              Administration
            </button>
            <button @click="handleLogout">Logout</button>
          </div>
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
  import { watch } from 'vue';
  import { useRouter } from 'vue-router';
  import { storeToRefs } from 'pinia';
  
  import { useAuthStore } from '../stores/authStore.js';
  import { useVersionStore } from '../stores/versionStore.js';
  import LoginModal from './LoginModal.vue';
  
  // Stores
  const authStore = useAuthStore();
  const versionStore = useVersionStore();
  
  // Router
  const router = useRouter();
  
  // Refs from stores
  const { showLoginModal } = storeToRefs(authStore);
  const { selectedProject } = storeToRefs(versionStore);
  
  // Watch project selection change
  watch(selectedProject, (newProject) => {
    if (newProject) {
      router.push(`/projects/${newProject}`);
    }
  });
  
  // Methods
  const goToProject = () => {
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
  </script>
  
  <style scoped>
  .navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    background-color: #eee;
  }
  
  .navbar-brand {
    font-weight: bold;
  }
  
  .navbar-menu {
    display: flex;
    align-items: center;
  }
  
  .project-selector {
    margin-right: 10px;
  }
  
  button {
    margin-left: 10px;
    padding: 5px 10px;
    cursor: pointer;
  }
  </style>
  