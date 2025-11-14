# 🏪 useAuthStore — Authentication Store

This **Pinia store** manages authentication, user information, project access, and API-related login state.  
It handles JWT tokens, user scopes, and provides utilities for login/logout and fetching project data.

---

## 🧩 State

| State | Type | Description |
|--------|------|-------------|
| **`token`** | `Ref<string \| null>` | Holds the current JWT authentication token. `null` if the user is logged out. |
| **`user`** | `Ref<User \| null>` | Contains decoded user information (username, email, and scopes). Loaded from `localStorage` if available. |
| **`allProjects`** | `Ref<string[]>` | List of all available project names. Persisted in `localStorage` for reuse. |
| **`showLoginModal`** | `Ref<boolean>` | Controls visibility of the login modal. Used by the UI to trigger the login dialog. |

> 🗂️ **Persistence:**  
> - `token`, `user`, and `allProjects` are synchronized with `localStorage` for session recovery between page reloads.  
> - The JWT is stored as `jwtToken`, user info as `user`, and project list as `allProjects`.

---

## 🧮 Getters

| Getter | Type | Description |
|---------|------|-------------|
| **`isAuthenticated`** | `Computed<boolean>` | Returns `true` if a JWT token exists (`!!token.value`). |
| **`isSuperAdmin`** | `Computed<boolean>` | Returns `true` if the user has the wildcard admin scope (`scopes['*'] === 'admin'`). |
| **`getUserProjects`** | `Computed<string[]>` | Returns the list of project IDs the user has explicit scopes for (excluding `"*"`). |
| **`isAdminForProject(project)`** | `(project: string) → boolean` | Checks if the user is an admin for the given project. |
| **`filteredProjects`** | `Computed<string[]>` | Returns: <br> - all projects if the user is a SuperAdmin, <br> - otherwise, only projects listed in `getUserProjects`. |

---

## ⚙️ Actions

| Action | Signature | Description |
|---------|------------|-------------|
| **`login(newToken)`** | `(newToken: string) → void` | Handles user login: <br> 1. Stores the new token in `token` and `localStorage`. <br> 2. Decodes the JWT into the `user` state. <br> 3. Closes the login modal. <br> 4. Calls `retryRequests(newToken)` to resume any pending API requests. |
| **`logout()`** | `() → void` | Logs the user out: <br> - Clears token, user, and projects. <br> - Removes all related entries from `localStorage`. |
| **`fetchProjects()`** | `() → Promise<void>` | Fetches the project list from the backend (`/api/v1/settings/projects`) using the authenticated API client. <br> - On success: stores the project list in state and `localStorage`. <br> - On failure: logs an error and resets the project list. |
| **`decodeToken()`** | `() → void` | Decodes the current JWT token (if any) and updates the `user` state. |

---

## 🔐 Behavior Summary

- Uses **JWT-based authentication**.
- On **login**, decodes and stores the token, making the user data and project scopes immediately available.
- Differentiates between **SuperAdmins** (`"*": "admin"`) and **project-specific admins**.
- Provides helper getters to control UI access (e.g., filtering projects, determining admin privileges).
- `fetchProjects()` synchronizes available projects with the backend and caches them locally.
- `logout()` cleans up all authentication and cached data.

---

## 🧠 Example Usage

```ts
const auth = useAuthStore()

if (!auth.isAuthenticated) {
  auth.showLoginModal = true
}

await auth.login(jwtToken)
console.log(auth.user?.username)

if (auth.isAdminForProject('project42')) {
  console.log('User has admin rights for project42')
}

await auth.fetchProjects()
console.log(auth.filteredProjects)
```

---

## 🌿 Related Diagram

A lifecycle diagram (`auth-store-lifecycle.puml`) is available to visualize how **token**, **user**, and **projects** flow through the store lifecycle.