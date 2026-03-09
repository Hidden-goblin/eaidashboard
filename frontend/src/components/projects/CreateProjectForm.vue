<script setup lang="ts">
import {ref} from "vue"
import {useLoadingStore} from "@/stores/loadingStore";
import {logger} from "@/composables/logger";
import {useEscapeToClose} from '@/composables/useEscapteToClose';
import BaseButton from "@/components/utils/BaseButton.vue";
import {createProject as createProjectService} from "@/services/projectService";

const emit = defineEmits(["close", "project-created"]);

const closeModal = () => emit('close');
useEscapeToClose(closeModal);

const projectName = ref("");
const error = ref("");

const loadingStore = useLoadingStore();

const createProject = async () => {
  logger.debug("Entering create project");
  loadingStore.startLoading();
  error.value = "";

  try {
    // POST new project
    await createProjectService(projectName.value);
    logger.debug(`Project ${projectName.value} created`);
    // emit and reset
    emit("project-created");
    logger.debug(`End of CreateProject`);
  } catch (err: any) {
    error.value = err.message
  } finally {
    loadingStore.stopLoading();
  }

  // })
}

</script>

<template>
  <teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal">
        <h3>Create New Project</h3>
        <form @submit.prevent="createProject">
          <div class="form-group">
            <label for="projectName">Project Name:</label>
            <input
                type="text"
                id="projectName"
                data-testid="projectNameInput"
                v-model="projectName"
                required
                placeholder="Enter project name"
            />
          </div>
          <div v-if="error" class="error" data-testid="errorProjectForm">{{ error }}</div>
          <div class="modal-actions">
            <BaseButton variant="create" type="submit" data-testid="createProjectButton">Create</BaseButton>
            <BaseButton variant="close" @click="closeModal" data-testid="cancelCreateProjectButton">Cancel</BaseButton>
          </div>
        </form>
      </div>
    </div>
  </teleport>
</template>

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