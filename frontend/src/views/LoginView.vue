<template>
  <div class="login-view">
    <h2>Login</h2>
    <form @submit.prevent="handleLogin" class="login-form">
      <div class="form-group">
        <label for="username">Username:</label>
        <input type="text" v-model="username" id="username" required autocomplete="username">
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" v-model="password" id="password" required autocomplete="current-password">
      </div>
      <div v-if="authStore.error" class="error-message">
        {{ authStore.error }}
      </div>
      <button type="submit" :disabled="authStore.isLoading" class="btn btn-primary">
        {{ authStore.isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../stores/authStore';
import { useRouter, useRoute } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute(); // To get query params like 'redirect'

const username = ref('');
const password = ref('');

const handleLogin = async () => {
  await authStore.login({ username: username.value, password: password.value });
  if (authStore.isAuthenticated) {
    // Redirect to the path the user was trying to access, or home page
    const redirectPath = route.query.redirect || '/';
    router.push(redirectPath);
  }
  // If login fails, error is in authStore.error and displayed in template
};
</script>

<style scoped>
.login-view {
  max-width: 350px;
  margin: 50px auto;
  padding: 25px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  background-color: #fff;
}
.login-view h2 {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}
.login-form .form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}
.form-group input[type="text"],
.form-group input[type="password"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.error-message {
  color: #d9534f; /* Bootstrap danger color */
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 15px;
  text-align: center;
  font-size: 0.9em;
}
.btn-primary {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}
.btn-primary:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}
.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}
</style>
