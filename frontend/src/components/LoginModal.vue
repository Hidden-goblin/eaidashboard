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
            v-model="password"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="errorMessage" class="error">
          {{ errorMessage }}
        </div>

        <div class="modal-actions">
          <button type="submit">Connect</button>
          <button type="button" @click="emit('close')">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useApiBaseUrl } from '../composables/useApiBaseUrl'

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
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(username.value)) {
    errorMessage.value = 'Please enter a valid email address.'
    return
  }

  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        username: username.value,
        password: password.value
      })
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Error logging in')
    }

    const data = await response.json()
    const token = data.access_token

    if (token) {
      authStore.login(token)
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
</style>
