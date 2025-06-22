<!-- src/components/versions/CreateVersionForm.vue -->
<template>
    <div class="modal-overlay" @click.self="$emit('cancel')">
      <div class="modal-content">
        <h3>Create New Version</h3>
        <form @submit.prevent="createVersion">
          <div class="form-group">
            <label for="versionName">Version Name:</label>
            <input
              type="text"
              id="versionName"
              v-model="versionName"
              required
              placeholder="Enter version name"
            />
          </div>
          <div v-if="error" class="error">{{ error }}</div>
          <div class="actions">
            <button type="submit">Create</button>
            <button type="button" @click="$emit('cancel')">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </template>

  <script>
  import {ref} from "vue";
  import { useAuthStore } from "../../stores/authStore.js";
  import { useApi } from "../../composables/useApi.js";
  import { useVersionStore } from "../../stores/versionStore";
  import {useApiBaseUrl} from "../../composables/useApiBaseUrl.js";

  export default {
    name: 'CreateVersionForm',
    props: {
      projectName: { type: String, required: true }
    },
    setup(props, { emit }) {
      const versionName = ref('');
      const error = ref('');
      const authStore = useAuthStore();
      const { fetchWithAuth } = useApi();
      const apiBaseUrl = useApiBaseUrl();

      const createVersion = () => {
        const url = `${apiBaseUrl}/api/v1/projects/${props.projectName}/versions`;

        fetchWithAuth(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authStore.token}`
          },
          body: JSON.stringify({ version: versionName.value })
        })
          .then((response) => {
            if (!response.ok) {
              return response.json().then((err) => {
                throw new Error(err.detail || 'Error creating version');
              });
            }
            return response.json();
          })
          .then(() => {
            return fetchWithAuth(`${url}/${versionName.value}`, {
              method: 'GET',
              headers: {
                Authorization: `Bearer ${authStore.token}`
              }
            });
          })
          .then((response) => {
            if (!response.ok) {
              throw new Error('Error fetching version details');
            }
            return response.json();
          })
          .then((data) => {
            emit('version-created', data); // Notify parent
            versionName.value = ''; // Reset
          })
          .catch((err) => {
            error.value = err.message;
          });
      };

      return { versionName, error, createVersion };
    },
  };
  </script>

  <style scoped>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-content {
    background: white;
    padding: 20px;
    border-radius: 12px;
    width: 400px;
    max-width: 90%;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  }

  .form-group {
    margin-bottom: 15px;
  }

  .form-group label {
    display: block;
    margin-bottom: 5px;
  }

  .form-group input {
    width: 100%;
    padding: 8px;
    box-sizing: border-box;
  }

  .actions {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
  }

  button {
    padding: 8px 16px;
    border: none;
    background: #3498db;
    color: white;
    border-radius: 4px;
    cursor: pointer;
  }

  button[type='button'] {
    background: #ccc;
  }

  button:hover {
    opacity: 0.9;
  }

  .error {
    color: red;
    margin-top: 10px;
  }
  </style>
