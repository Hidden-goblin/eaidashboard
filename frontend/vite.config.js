import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  test: { // Add this test configuration
    globals: true,
    environment: 'happy-dom', // Use happy-dom or 'jsdom'
    setupFiles: './src/setupTests.js', // Optional setup file
  },
  // Ensure other configurations like base are preserved if they existed
  // For this project, base was implicitly '/'
  base: '/',
  build: {
    rollupOptions: {
      output: {
        // Redirige tous les assets vers le dossier "fassets"
        assetFileNames: 'fassets/[name].[hash][extname]',
        chunkFileNames: 'fassets/[name].[hash].js',
        entryFileNames: 'fassets/[name].[hash].js',
      }
    }
  }
});
