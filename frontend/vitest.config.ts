import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
    plugins: [vue()],
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './vitest.setup.js',
        assertions: {
            globals: true,
        },
        // Output directories for reports
        reporters: [
            'default', // Console output
            ['junit', {
                outputFile: 'test-results/results.xml' // JUnit format
            }],
            ['html', {
                outputFolder: 'test-results/html',     // HTML report
                open: false                            // Don't open browser after run
            }]
        ],

        // Directory where snapshots and coverage live
        outputFile: {
            html: 'test-results/html/index.html',
            junit: 'test-results/results.xml',
        },

        coverage: {
            reporter: ['text', 'html'],
            reportsDirectory: 'test-results/coverage'
        }
    },
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src')
        }
    }
});
