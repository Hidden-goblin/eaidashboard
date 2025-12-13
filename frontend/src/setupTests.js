// import { config } from '@vue/test-utils';
// Example: Mock global properties or provide plugins if necessary
// config.global.mocks['$t'] = (key) => key; // Example for mocking vue-i18n
import '@testing-library/jest-dom'
import {logger} from "./composables/logger.js";
// This file can be used for global setup for tests.
// For example, setting up mocks for browser APIs not available in happy-dom/jsdom,
// or configuring testing libraries.
logger.info('Vitest setup file loaded.');
