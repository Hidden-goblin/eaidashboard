# Deployment Guide

This guide provides instructions for building and deploying the Vue.js frontend application.

## Building the Application

1.  Navigate to the `frontend` directory: `cd frontend`
2.  Install dependencies: `npm install` (or `yarn install`)
3.  Build the application: `npm run build` (or `yarn build`)

The production-ready static assets will be generated in the `frontend/dist` directory.

## Configuration

### API Base URL

The application connects to a backend API. The base URL for this API is configured at build time using the `VITE_API_BASE_URL` environment variable.

-   **Default (from `.env`):** If not set during build, it defaults to the value specified in `frontend/.env` (e.g., `/api/v1`). This is suitable for deployments where the API is served from the same domain under that prefix.
-   **Build-time Override:** You can override this during the build process:
    ```bash
    VITE_API_BASE_URL=/my/custom/api/prefix npm run build
    ```
    Or for an absolute path (ensure CORS is handled by the backend):
    ```bash
    VITE_API_BASE_URL=https://api.example.com/v1 npm run build
    ```

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
