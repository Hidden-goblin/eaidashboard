<template>
    <div class="admin-container">
      <h1>Administration Panel</h1>
      
      <!-- Create New User Section -->
      <section class="create-user">
        <h2>Create New User</h2>
        <form @submit.prevent="createUser">
          <div>
            <label>Email:</label>
            <input type="email" v-model="newUser.email" required />
          </div>
          <!-- For Super Admin, allow project selection -->
          <div v-if="isSuperAdmin">
            <label>Project:</label>
            <select v-model="newUser.project">
              <option value="">System-wide</option>
              <option v-for="proj in allProjects" :key="proj" :value="proj">{{ proj }}</option>
            </select>
          </div>
          <!-- For project admin, show the project (read-only) -->
          <div v-else>
            <label>Project:</label>
            <input type="text" :value="adminProjects[0]" disabled />
          </div>
          <button type="submit">Create User</button>
        </form>
      </section>
      
      <!-- List Users Section -->
      <section class="list-users">
        <h2>List Users</h2>
        <button @click="listUsers">Refresh List</button>
        <ul>
          <li v-for="user in users" :key="user.id">
            {{ user.email }} - Project: {{ user.project }}
            <button @click="selectUser(user)">Edit</button>
          </li>
        </ul>
      </section>
      
      <!-- Update User Section -->
      <section class="update-user" v-if="selectedUser">
        <h2>Update User</h2>
        <form @submit.prevent="updateUser">
          <div>
            <label>Email:</label>
            <input type="email" v-model="selectedUser.email" required />
          </div>
          <!-- Super Admin can reassign project -->
          <div v-if="isSuperAdmin">
            <label>Project:</label>
            <select v-model="selectedUser.project">
              <option value="">System-wide</option>
              <option v-for="proj in allProjects" :key="proj" :value="proj">{{ proj }}</option>
            </select>
          </div>
          <button type="submit">Update User</button>
        </form>
      </section>
      
      <!-- Create New Project Section (Super Admin only) -->
      <section class="create-project" v-if="isSuperAdmin">
        <h2>Create New Project</h2>
        <form @submit.prevent="createProject">
          <div>
            <label>Project Name:</label>
            <input type="text" v-model="newProject.name" required />
          </div>
          <button type="submit">Create Project</button>
        </form>
      </section>
    </div>
  </template>
  
  <script>
  export default {
    name: "Administration",
    data() {
      return {
        token: null,
        jwtData: {},
        newUser: {
          email: '',
          project: ''
        },
        newProject: {
          name: ''
        },
        users: [],
        selectedUser: null,
        // Dummy list of projects; in a real app, fetch this from your backend.
        allProjects: ['Project1', 'Project2', 'Project3']
      }
    },
    computed: {
      // Super Admin if the global right "*" equals "admin"
      isSuperAdmin() {
        return this.jwtData['*'] === 'admin';
      },
      // List of projects where the user has 'admin' rights (for project administrators)
      adminProjects() {
        let projects = [];
        for (const key in this.jwtData) {
          if (key !== 'username' && key !== '*' && this.jwtData[key] === 'admin') {
            projects.push(key);
          }
        }
        return projects;
      }
    },
    created() {
      this.token = localStorage.getItem('jwtToken');
      if (this.token) {
        this.decodeJWT();
      } else {
        // Optionally redirect to login if token is missing.
        this.$router.push('/');
      }
    },
    methods: {
      decodeJWT() {
        try {
          const payload = this.token.split('.')[1];
          this.jwtData = JSON.parse(atob(payload));
        } catch (e) {
          console.error('Invalid token', e);
        }
      },
      createUser() {
        // For project admin, use the first admin project.
        let project = this.isSuperAdmin ? this.newUser.project : this.adminProjects[0];
        // Simulate an API call to create a user.
        console.log(`Creating user ${this.newUser.email} for project: ${project}`);
        // Reset the form fields.
        this.newUser.email = '';
        this.newUser.project = '';
        alert('User created (simulation).');
      },
      listUsers() {
        // Simulate an API call to fetch users.
        if (this.isSuperAdmin) {
          // Simulated: fetch all users.
          this.users = [
            { id: 1, email: 'user1@example.com', project: 'Project1' },
            { id: 2, email: 'user2@example.com', project: 'Project2' },
            { id: 3, email: 'user3@example.com', project: 'Project3' }
          ];
        } else {
          // Simulated: fetch users only for the admin's project.
          let project = this.adminProjects[0];
          this.users = [
            { id: 1, email: 'user1@example.com', project },
            { id: 4, email: 'user4@example.com', project }
          ];
        }
      },
      selectUser(user) {
        // Create a shallow copy to avoid mutating the list directly.
        this.selectedUser = { ...user };
      },
      updateUser() {
        // Simulate an API call to update the user.
        console.log(`Updating user ${this.selectedUser.email} with project: ${this.selectedUser.project}`);
        alert('User updated (simulation).');
        this.selectedUser = null;
        this.listUsers();
      },
      createProject() {
        // This function should only be accessible for Super Admin.
        if (!this.isSuperAdmin) return;
        console.log(`Creating new project: ${this.newProject.name}`);
        alert('Project created (simulation).');
        // Optionally update the local projects list.
        this.allProjects.push(this.newProject.name);
        this.newProject.name = '';
      }
    }
  }
  </script>
  
  <style scoped>
  .admin-container {
    padding: 20px;
  }
  section {
    margin-bottom: 30px;
    border: 1px solid #ccc;
    padding: 15px;
  }
  section h2 {
    margin-top: 0;
  }
  form div {
    margin-bottom: 10px;
  }
  label {
    display: inline-block;
    width: 120px;
  }
  input, select {
    padding: 5px;
  }
  button {
    padding: 5px 10px;
    cursor: pointer;
  }
  </style>
  