<template>
  <div class="layout">
    <header class="app-header">
      <NavBar />
    </header>
    <main class="app-content">
      <router-view />
    </main>
    <footer class="app-footer">
      <p>&copy; 2025 EAIDashboard</p>
    </footer>
  </div>
</template>

<script setup>
import  NavBar from '../components/NavBar.vue';

</script>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.app-header {
  background-color: #f0f0f0;
  padding: 1rem;
  text-align: center;
}
.app-header nav {
  margin-bottom: 10px;
}
.app-header nav a, .app-header nav button.logout-button {
  margin: 0 10px;
  text-decoration: none;
  color: #333;
  font-weight: bold;
  padding: 5px 10px;
  border-radius: 4px;
}
.app-header nav a.router-link-exact-active {
  color: #42b983;
  background-color: #e0f2e9;
}
.app-header nav button.logout-button {
  background-color: #ff6b6b;
  color: white;
  border: none;
  cursor: pointer;
}
.app-header nav button.logout-button:hover {
  background-color: #e05252;
}
.user-info {
  font-size: 0.9em;
  color: #555;
}
.app-content {
  flex-grow: 1;
  padding: 1rem;
}
.app-footer {
  background-color: #333;
  color: white;
  padding: 1rem;
  text-align: center;
  font-size: 0.9em;
}
</style>
