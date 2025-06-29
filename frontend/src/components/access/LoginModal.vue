<!-- src/components/LoginModal.vue -->
<template>
  <div class="modal-overlay">
    <div class="modal">
      <h2>Login</h2>
      <form @submit.prevent="connect">
        <div>
          <label for="username">Email:</label>
          <input
            type="email"
            id="username"
            data-testid="username-input"
            v-model="username"
            required
            autocomplete="username"
          />
        </div>
        <div>
          <label for="password">Password:</label>
          <input
            type="password"
            id="password"
            data-testid="password-input"
            v-model="password"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="errorMessage" class="error">
          {{ errorMessage }}
        </div>

        <div class="modal-actions">
          <BaseButton type="submit">Connect</BaseButton>
          <BaseButton @click="emit('close')">Cancel</BaseButton>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../../stores/authStore.js'
import { useApiBaseUrl } from '../../composables/useApiBaseUrl.js'
import BaseButton from "../utils/BaseButton.vue";

// Props / Emits
const emit = defineEmits(['close', 'login-success'])

// State
const username = ref('')
const password = ref('')
const errorMessage = ref('')

// Stores & config
const authStore = useAuthStore()
const apiBaseUrl = useApiBaseUrl()

// Methods
const connect = async () => {
  console.log('in connect', username.value, password.value)
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(username.value)) {
    errorMessage.value = 'Please enter a valid email address.'
    return
  }
  console.log('fetching token from', `${apiBaseUrl}/api/v1/token`)
  try {
    const formBody =
        'username=' + encodeURIComponent(username.value) +
        '&password=' + encodeURIComponent(password.value)

    const response = await fetch(`${apiBaseUrl}/api/v1/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body:formBody
      })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Error logging in')
    }
    console.log('response ok')
    const data = await response.json()
    const token = data.access_token

    if (token) {
      authStore.login(token)
      console.log('token', token)
      emit('login-success', token)
    }
  } catch (err) {
    errorMessage.value = err.message
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  min-width: 300px;
}

.modal-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.error {
  color: red;
  margin-top: 10px;
}
form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

form > div {
  display: flex;
  align-items: center;
}

label {
  width: 100px; /* or any fixed width that fits your labels */
  text-align: left;
  margin-right: 10px;
  font-weight: bold;
}

input {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
input:focus {
  outline: none;
  border-color: #3490dc;
  box-shadow: 0 0 0 2px rgba(52, 144, 220, 0.2);
}
</style>
