<template>
  <Layout />
</template>

<script setup>
import Layout from './components/Layout.vue';
import { useAuthStore } from './stores/authStore';
import { onMounted } from 'vue';

const authStore = useAuthStore();

onMounted(async () => {
  // Check authentication status when the app is mounted
  // This is crucial for restoring session if user previously logged in
  // and token is still valid/present.
  await authStore.checkAuth();
});
</script>

<style>
/* Global styles can go here or in a separate CSS file imported in main.js */
body {
  margin: 0;
  font-family: Avenir, Helvetica, Arial, sans-serif; /* Consider moving to Layout.vue or a global CSS */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50; /* Default text color */
  background-color: #f4f7f6; /* A light background for the whole app */
}

/* Basic reset or global settings */
#app {
  /* This is the root element Vue mounts to in index.html */
  /* Styles here apply if Layout.vue doesn't cover full viewport or has transparent background */
}

/* Global link styles if not overridden by component styles */
a {
  /* color: #007bff; */ /* Example global link color */
  /* text-decoration: none; */
}
/* a:hover { */
  /* text-decoration: underline; */
/* } */
</style>
