<template>
  <div class="users-view">
    <h2>User Management</h2>
    <div class="actions">
      <button @click="openCreateUserModal" class="btn btn-primary">Add New User</button>
    </div>

    <!-- Create/Edit User Modal -->
    <div v-if="showUserModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeUserModal">&times;</span>
        <h5>{{ editingUser ? 'Edit User' : 'Add New User' }}</h5>
        <form @submit.prevent="handleSaveUser">
          <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" v-model="currentUser.username" required :disabled="!!editingUser" />
          </div>
          <div class="form-group">
            <label for="password">{{ editingUser ? 'New Password (leave blank to keep current)' : 'Password:' }}</label>
            <input type="password" id="password" v-model="currentUser.password" :required="!editingUser" />
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="currentUser.isAdmin" /> Is Admin
            </label>
          </div>
          <!-- Add more fields like email, full_name if your API supports them -->
          <div v-if="userStore.error" class="error-message">{{ userStore.error }}</div>
          <button type="submit" :disabled="userStore.isLoading" class="btn btn-success">
            {{ userStore.isLoading ? 'Saving...' : 'Save User' }}
          </button>
          <button type="button" @click="closeUserModal" class="btn btn-link">Cancel</button>
        </form>
      </div>
    </div>

    <div v-if="userStore.isLoading && userStore.users.length === 0" class="loading">Loading users...</div>
    <div v-if="userStore.error && !showUserModal" class="error-message">{{ userStore.error }}</div>

    <table v-if="userStore.users.length > 0" class="users-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Is Admin</th>
          <th>Joined At</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in userStore.users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td><span :class="user.isAdmin ? 'badge badge-success' : 'badge badge-secondary'">{{ user.isAdmin ? 'Yes' : 'No' }}</span></td>
          <td>{{ formatDate(user.created_at || user.join_date || user.registered_at) }}</td>
          <td>
            <button @click="openEditUserModal(user)" class="btn btn-xs btn-info">Edit</button>
            <button @click="confirmDeleteUser(user.id)" class="btn btn-xs btn-danger" :disabled="userStore.isLoading">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!userStore.isLoading && userStore.users.length === 0 && !userStore.error" class="no-data">
      No users found.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useUserStore } from '../stores/userStore';

const userStore = useUserStore();
const showUserModal = ref(false);
const editingUser = ref(null); // Stores the full user object when editing
const currentUser = reactive({ id: null, username: '', password: '', isAdmin: false });

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString();
};

const resetCurrentUserForm = () => {
  currentUser.id = null;
  currentUser.username = '';
  currentUser.password = '';
  currentUser.isAdmin = false;
  userStore.error = null; // Clear any previous form errors from the store
};

const openCreateUserModal = () => {
  resetCurrentUserForm();
  editingUser.value = null;
  showUserModal.value = true;
};

const openEditUserModal = (user) => {
  editingUser.value = user; // Keep the original user object
  // Populate form fields from user object
  currentUser.id = user.id;
  currentUser.username = user.username;
  currentUser.password = ''; // Password field should be blank for editing
  currentUser.isAdmin = user.isAdmin;
  userStore.error = null; // Clear previous errors
  showUserModal.value = true;
};

const closeUserModal = () => {
  showUserModal.value = false;
  editingUser.value = null;
  resetCurrentUserForm();
};

const handleSaveUser = async () => {
  const userData = {
    username: currentUser.username,
    isAdmin: currentUser.isAdmin,
  };
  // Only include password if it's a new user or if the password field is not empty for an existing user
  if (!editingUser.value || (editingUser.value && currentUser.password)) {
    userData.password = currentUser.password;
  }

  try {
    if (editingUser.value) {
      await userStore.updateUser(editingUser.value.id, userData);
    } else {
      await userStore.createUser(userData);
    }
    closeUserModal();
    // userStore.fetchUsers(); // Optionally re-fetch all users, or rely on optimistic update
  } catch (e) {
    // Error is set in the store and displayed in the modal
    // No need to console.error here as store action does it
  }
};

const confirmDeleteUser = async (userId) => {
    if (confirm(`Are you sure you want to delete user ID ${userId}? This action cannot be undone.`)) {
        try {
            await userStore.deleteUser(userId);
            // List updates optimistically in store
        } catch (e) {
            // Error handled in store, could show a global notification here if desired
            alert(`Error deleting user: ${userStore.error}`);
        }
    }
};

onMounted(() => {
  userStore.fetchUsers();
});
</script>

<style scoped>
.users-view { padding: 20px; }
.actions { margin-bottom: 20px; }
.modal {
  position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
  overflow: auto; background-color: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
}
.modal-content {
  background-color: #fefefe; padding: 20px; border: 1px solid #888;
  width: 80%; max-width: 500px; border-radius: 8px; position: relative;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.close {
  color: #aaa; position: absolute; top: 10px; right: 15px;
  font-size: 28px; font-weight: bold; cursor: pointer;
}
.close:hover, .close:focus { color: black; text-decoration: none; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
.form-group input[type="text"],
.form-group input[type="password"],
.form-group input[type="checkbox"] {
  width: calc(100% - 22px); padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;
}
.form-group input[type="checkbox"] { width: auto; margin-right: 5px; }
.users-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
.users-table th, .users-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
.users-table th { background-color: #f0f0f0; font-weight: bold; }
.loading, .no-data { text-align: center; padding: 20px; font-size: 1.1em; color: #777; }
.error-message { color: #d9534f; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 10px; margin-bottom: 15px; }
.btn { padding: 8px 12px; border-radius: 4px; cursor: pointer; border: none; font-size: 0.9em; margin-right: 5px; }
.btn-primary { background-color: #007bff; color: white; }
.btn-success { background-color: #28a745; color: white; }
.btn-info { background-color: #17a2b8; color: white; }
.btn-danger { background-color: #dc3545; color: white; }
.btn-link { background-color: transparent; color: #007bff; text-decoration: underline; }
.btn-xs { padding: 4px 8px; font-size: 0.8em; }
.badge { display: inline-block; padding: .25em .4em; font-size: 75%; font-weight: 700; line-height: 1; text-align: center; white-space: nowrap; vertical-align: baseline; border-radius: .25rem; }
.badge-success { color: #fff; background-color: #28a745; }
.badge-secondary { color: #fff; background-color: #6c757d; }
</style>
