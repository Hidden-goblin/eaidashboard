<template>
  <div class="layout">
    <header class="app-header">
      <h1>My Application</h1>
      <nav>
        <router-link to="/">Dashboard</router-link>
        <router-link to="/projects">Projects</router-link>
        <router-link v-if="authStore.user && authStore.user.isAdmin" to="/users">Users</router-link>
        <router-link to="/documentation">Documentation</router-link>
        <!-- Login/Logout Links -->
        <router-link v-if="!authStore.isAuthenticated" to="/login">Login</router-link>
        <button v-if="authStore.isAuthenticated" @click="handleLogout" class="logout-button">Logout</button>
      </nav>
      <div v-if="authStore.isAuthenticated && authStore.user" class="user-info">
        Logged in as: {{ authStore.user.username }} ({{ authStore.user.isAdmin ? 'Admin' : 'User' }})
      </div>
    </header>
    <main class="app-content">
      <router-view />
    </main>
    <footer class="app-footer">
      <p>&copy; 2023 My Application</p>
    </footer>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/authStore';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
  router.push('/login'); // Redirect to login after logout
};
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
