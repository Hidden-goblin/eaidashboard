<!-- src/components/LoginModal.vue -->
<template>
  <teleport to="body">
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
  </teleport>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useAuthStore} from '@/stores/authStore'
import {useApiBaseUrl} from '@/composables/useApiBaseUrl'
import BaseButton from "@/components/utils/BaseButton.vue";
import {logger} from "@/composables/logger";

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
  logger.debug('Connecting')
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(username.value)) {
    errorMessage.value = 'Please enter a valid email address.'
    return
  }
  logger.debug('fetching token from', `${apiBaseUrl}/api/v1/token`)
  const formBody =
      'username=' + encodeURIComponent(username.value) +
      '&password=' + encodeURIComponent(password.value);

  try {
    await authStore.login( formBody);
    emit('login-success', 'connected')
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
  z-index: 9999;
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
