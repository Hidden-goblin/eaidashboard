# Testing Guide

This document provides instructions for running unit tests and outlines a strategy for integration testing the Vue.js frontend application.

## Unit Tests

Unit tests are written using [Vitest](https://vitest.dev/) and [Vue Test Utils](https://test-utils.vuejs.org/).

### Prerequisites
- Ensure you are in the `frontend` directory.
- Install dependencies if you haven't already: `npm install`

### Running Unit Tests
- **Run all tests in watch mode:**
  ```bash
  npm test
  # or
  npm run test
  ```
- **Run all tests once:**
  ```bash
  npm run test -- run
  # This is equivalent to: vitest run
  ```
- **Run tests with a UI (interactive mode):**
  ```bash
  npm run test:ui
  # This is equivalent to: vitest --ui
  ```
- **Generate coverage report:**
  ```bash
  npm run coverage
  # This is equivalent to: vitest run --coverage
  ```
  The coverage report will typically be found in the `frontend/coverage/` directory. To enable coverage, you might need to add `coverage: { provider: 'v8' }` (or 'istanbul') to your `vite.config.js` test options.

### Test File Location
Test files are typically located in `__tests__` subdirectories alongside the files they test (e.g., `frontend/src/components/__tests__/MyComponent.spec.js` or `frontend/src/stores/__tests__/myStore.spec.js`). The example tests are in:
- `frontend/src/views/__tests__/LoginView.spec.js`
- `frontend/src/stores/__tests__/authStore.spec.js`

A `frontend/src/setupTests.js` file is available for global test setup if needed.

## Integration Testing Strategy (Manual)

Integration testing ensures that different parts of the application work together correctly, including interaction with the backend API. As automated E2E tests are not set up in this phase, manual integration testing is crucial.

**Environment:**
- A running instance of the backend API.
- The frontend application served (e.g., using `npm run dev` for development or built assets on a server).

**API URL Configuration for Testing:**
The frontend determines the API base URL with the following precedence (see `DEPLOYMENT.md` for full details):
1. `VITE_API_BASE_URL` (absolute, set at build time).
2. `VITE_API_BASE_URL` (relative, set at build time).
3. Dynamically: `[frontend_protocol]//[frontend_hostname]:8087` (at runtime if `VITE_API_BASE_URL` is not set or empty).
4. Default fallback (e.g., `/api/v1`).

*Ensure your test environment is configured accordingly:*
- If you rely on the dynamic same-host URL (option 3), your backend API **must** be running on the same host as the frontend and accessible on port **8087** using the same protocol (HTTP/HTTPS).
- Alternatively, for more control, set the `VITE_API_BASE_URL` environment variable to the correct API endpoint when building or serving the frontend for your test environment. For example:
  ```bash
  # For Vite dev server
  VITE_API_BASE_URL=http://localhost:3000/api npm run dev
  # For a test build
  VITE_API_BASE_URL=https://test-api.example.com/v1 npm run build
  ```
This ensures the frontend targets the correct backend during tests.

**Key Areas to Test:**

1.  **Authentication:**
    *   [ ] User can successfully log in with valid admin credentials (e.g., admin/admin).
    *   [ ] User can successfully log in with valid non-admin credentials (e.g., user/user).
    *   [ ] User sees an error message with invalid credentials.
    *   [ ] User is redirected to the login page when accessing protected routes without authentication.
    *   [ ] Admin users see admin-specific UI elements (e.g., "Users" link in nav).
    *   [ ] Non-admin users do not see admin-specific UI elements and are redirected if they try to access admin routes (e.g., /users).
    *   [ ] User can successfully log out; session is cleared, and user is redirected to login.
    *   [ ] Session/token is managed correctly (e.g., on page refresh, user remains logged in if token is valid).

2.  **Dashboard:**
    *   [ ] Dashboard loads and displays project/version summaries correctly after login.
    *   [ ] Data displayed (mocked or from API) is accurate.

3.  **Project Management:**
    *   [ ] User can view a list of projects.
    *   [ ] Admin user can create a new project.
    *   [ ] Non-admin user cannot create a new project (if `project-create` route is admin-restricted).
    *   [ ] User can navigate to a project's detail view.
    *   [ ] Project detail view shows correct information and tabs (Versions, Tickets, Bugs, Campaigns, Repository).

4.  **Version Management (within a Project):**
    *   [ ] User can view a list of versions for a project.
    *   [ ] User can add a new version to a project.
    *   [ ] Version details are displayed correctly.

5.  **Ticket Management (within a Version):**
    *   [ ] User can view tickets for a specific project version.
    *   [ ] User can create a new ticket.
    *   [ ] User can edit an existing ticket.
    *   [ ] Ticket data is saved and displayed correctly.

6.  **Bug Management (within a Project):**
    *   [ ] User can view bugs for a project.
    *   [ ] Filtering bugs (by version, status) works as expected.
    *   [ ] User can create a new bug.
    *   [ ] User can edit an existing bug.
    *   [ ] Bug data is saved and displayed correctly.

7.  **Campaign Management (within a Project):**
    *   [ ] User can view a list of campaigns for a project.
    *   [ ] User can create a new campaign, associating it with a version.
    *   [ ] Basic campaign details are displayed correctly.
    *   [ ] Navigation to placeholder "View Board" works.

8.  **Repository Management (within a Project):**
    *   [ ] User can import scenarios from a CSV file (mock success/failure).
    *   [ ] User can browse epics, features, and scenarios.
    *   [ ] Data displayed matches repository content (mocked).

9.  **User Management (Admin only):**
    *   [ ] Admin can view a list of all users.
    *   [ ] Admin can create a new user.
    *   [ ] Admin can edit an existing user (including admin status).
    *   [ ] Admin can delete a user.
    *   [ ] Changes are reflected correctly.

10. **Documentation View:**
    *   [ ] User can navigate to the documentation section.
    *   [ ] List of documentation topics is displayed.
    *   [ ] Selecting a topic displays its content correctly (Markdown rendered as HTML).
    *   [ ] Direct linking to documentation pages via URL query params works.

11. **General:**
    *   [ ] Application is responsive and UI elements are displayed correctly on different screen sizes (conceptual).
    *   [ ] No console errors in the browser during typical usage.
    *   [ ] Loading states and error messages are displayed appropriately throughout the application.
    *   [ ] Navigation between different sections is smooth and URLs update correctly.

This checklist should be expanded with more specific test cases based on the application's requirements and actual API responses.
        ```
