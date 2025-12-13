<template>
  <GlobalLoading />
  <Layout />
</template>

<script setup>
import Layout from './views/Layout.vue';
import { useAuthStore } from '@/stores/authStore';
import { onMounted } from 'vue';
import GlobalLoading from "@/components/utils/GlobalLoading.vue";
import { storeToRefs } from 'pinia'
import { useAuthEvents } from '@/composables/useAuthEvents'

const authStore = useAuthStore();
const { showLoginModal } = storeToRefs(authStore)
const { onUnauthorized } = useAuthEvents()

onMounted( () => {
  onUnauthorized(() => {
    showLoginModal.value = true;
  })
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
