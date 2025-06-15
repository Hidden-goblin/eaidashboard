# Deployment Guide

This guide provides instructions for building and deploying the Vue.js frontend application.

## Building the Application

1.  Navigate to the `frontend` directory: `cd frontend`
2.  Install dependencies: `npm install` (or `yarn install`)
3.  Build the application: `npm run build` (or `yarn build`)

The production-ready static assets will be generated in the `frontend/dist` directory.

## Configuration

### API Base URL

The application connects to a backend API. The base URL for this API is determined using the following order of precedence:

1.  **Absolute URL via Environment Variable (Build Time):**
    If `VITE_API_BASE_URL` is set to an absolute URL (e.g., `https://api.example.com/v1`) during the build process, this URL will be used directly.
    ```bash
    VITE_API_BASE_URL=https://api.example.com/v1 npm run build
    ```
    This is useful if your API is hosted on a completely different domain. Ensure CORS is correctly configured on your backend.

2.  **Relative Path via Environment Variable (Build Time):**
    If `VITE_API_BASE_URL` is set to a relative path (e.g., `/my/custom/api/prefix` or `/api/v1`) during the build process, this path will be used. Note that if `VITE_API_BASE_URL` is set to an empty string or a very generic value like `/api` (which might have been a previous default), the system might prioritize the dynamic URL (see next point).
    ```bash
    VITE_API_BASE_URL=/my/custom/api/prefix npm run build
    ```
    This is suitable for deployments where the API is served from the same domain as the frontend, possibly under a specific path managed by a reverse proxy.

3.  **Dynamic Same-Host URL (Runtime):**
    If `VITE_API_BASE_URL` is **not set** or is an empty string or a generic default like `/api` at build time, the frontend will attempt to construct the API URL dynamically at runtime using the `useApiBaseUrl.js` composable. It assumes the API is running on the **same hostname** as the frontend, but on **port 8087**.
    The URL will be: `[current_protocol]//[current_hostname]:8087`.
    For example, if you access the frontend at `http://localhost:5173` (Vite dev server) or `https://app.yourdomain.com`, it will try to reach the API at `http://localhost:8087` or `https://app.yourdomain.com:8087` respectively.
    This mode requires no special build-time configuration for the API URL if your development or deployment setup matches this convention (API on port 8087, same host).

4.  **Default Fallback (if all else fails or in non-browser test environments):**
    As a last resort, if the dynamic URL generation using `useApiBaseUrl()` is not possible (e.g., `window.location` is not available in certain test environments without proper mocking) and `VITE_API_BASE_URL` was not set or applicable, the `apiService.js` has a final fallback to a pre-defined relative path like `/api/v1`. It's best to ensure one of the above methods correctly resolves the API URL for your environment.

**Recommendation:**
*   For most production deployments using a reverse proxy to serve both frontend and API under the same domain, setting `VITE_API_BASE_URL` to a relative path like `/api/v1` (matching your proxy configuration) is recommended at build time.
*   The dynamic same-host URL (port 8087) can be very convenient for local development if your backend server runs on port 8087 and the frontend is served by Vite's dev server (default port 5173).

### Vue Router (`createWebHistory`)

This application uses Vue Router with `createWebHistory` for clean URLs (without `#`). This requires specific server-side configuration to ensure that all routes are correctly handled by the `index.html` file, allowing Vue Router to manage client-side navigation.

If you are deploying the contents of the `dist` directory to a static server, you need to configure the server to redirect all requests to `index.html` if a requested file is not found. This is a common setup for Single Page Applications (SPAs).

**Example Nginx Configuration:**
```nginx
server {
  listen 80;
  server_name yourdomain.com;
  root /path/to/your/frontend/dist; # Path to the dist directory
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  # Add other configurations like SSL, logs, etc.
}
```

**Example Apache Configuration (using `.htaccess`):**
Place a `.htaccess` file in your `dist` directory (or the directory it's served from) with the following content:
```apache
RewriteEngine On
# If the application is in a subdirectory, set RewriteBase /your-subdirectory/
RewriteBase /
RewriteRule ^index\.html$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]
```

### Deploying to a Subdirectory

If the application is not deployed at the root of your domain (e.g., `https://example.com/my-vue-app/`), you need to configure the `base` path in `frontend/vite.config.js` before building:

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  base: '/my-vue-app/' // Set this to your subdirectory
});
```
Then rebuild the application. The `BASE_URL` for the Vue Router will also be correctly set by Vite based on this `base` configuration.
