<template>
  <div class="layout">
    <header class="app-header">
      <!-- Placeholder for global navigation or branding -->
      <h1>My Application</h1>
      <nav>
        <router-link to="/">Dashboard</router-link>
        <router-link to="/projects">Projects</router-link>
        <router-link to="/users">Users</router-link>
        <router-link to="/documentation">Documentation</router-link>
        <!-- Add more links as new sections are implemented -->
      </nav>
    </header>
    <main class="app-content">
      <router-view />
    </main>
    <footer class="app-footer">
      <!-- Placeholder for footer content -->
      <p>&copy; 2023 My Application</p>
    </footer>
  </div>
</template>

<script setup>
// No specific script needed for this basic layout
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
.app-header nav a {
  margin: 0 15px;
  text-decoration: none;
  color: #333;
}
.app-header nav a.router-link-exact-active {
  color: #42b983;
  font-weight: bold;
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
}
</style>
