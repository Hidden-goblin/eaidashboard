import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
    // Load all environment variables for the current mode
    const env = loadEnv(mode, process.cwd())

    // Ensure VITE_RUN_TYPE is always defined (fallback to mode)
    const viteRunType = env.VITE_RUN_TYPE || mode

    console.log(`🏗️  Building Vite project in mode: ${mode} (VITE_RUN_TYPE=${viteRunType})`)

    return {
        plugins: [vue()],
        test: {
            globals: true,
            environment: 'happy-dom',
            setupFiles: './src/setupTests.js',
        },
        base: '/',
        build: {
            rollupOptions: {
                output: {
                    // Redirect all assets to folder "fassets"
                    assetFileNames: 'fassets/[name].[hash][extname]',
                    chunkFileNames: 'fassets/[name].[hash].js',
                    entryFileNames: 'fassets/[name].[hash].js',
                },
            },
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, 'src'),
            },
        },
        define: {
            // Inject VITE_RUN_TYPE so it's accessible to your frontend code
            'import.meta.env.VITE_RUN_TYPE': JSON.stringify(viteRunType),
        },
    }
})
