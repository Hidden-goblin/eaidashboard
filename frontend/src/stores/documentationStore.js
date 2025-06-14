import { defineStore } from 'pinia';
import apiService from '../services/apiService'; // Assuming this will be used for real API calls
import { marked } from 'marked'; // Import marked

export const useDocumentationStore = defineStore('documentation', {
  state: () => ({
    docFiles: [], // List of available .md files {name: 'index.md', title: 'Index'}
    currentDocContent: '', // Will store HTML converted from markdown
    currentDocName: null, // To keep track of the currently loaded document filename
    isLoading: false,
    error: null,
  }),
  actions: {
    async fetchDocFiles() {
      this.isLoading = true;
      this.error = null;
      try {
        // const data = await apiService.get('/documentation/files'); // Real API call
        // this.docFiles = data.files || data;

        // Mocking for now:
        await new Promise(resolve => setTimeout(resolve, 200)); // Simulate API call
        this.docFiles = [
          { name: 'index.md', title: 'Overview' },
          { name: '00-how_to.md', title: 'How To Guides' },
          { name: '00-monitoring.md', title: 'Monitoring' },
          { name: 'project_setup.md', title: 'Project Setup' },
          { name: 'bug_tracking.md', title: 'Bug Tracking Process' },
        ];
      } catch (e) {
        this.error = e.message || 'Failed to fetch documentation file list.';
        this.docFiles = [];
        console.error("fetchDocFiles error:", e);
      } finally {
        this.isLoading = false;
      }
    },
    async fetchDocContent(filename) {
      if (this.currentDocName === filename && this.currentDocContent && !this.error) {
        // Avoid re-fetching if already loaded, unless forced.
        // return;
      }
      this.isLoading = true;
      this.error = null;
      this.currentDocContent = '';
      this.currentDocName = filename;

      try {
        // const rawMarkdown = await apiService.getText(`/documentation/raw/${filename}`);
        // apiService would need a method like `getText` that doesn't assume JSON response.
        // For now, using mock data:
        await new Promise(resolve => setTimeout(resolve, 200)); // Simulate API call
        let rawMarkdown = `# ${filename}\n\nThis is default content for ${filename}.\n\nPlease select a topic from the sidebar or ensure the backend API is configured.`;

        // Example mock content (can be expanded)
        if (filename === 'index.md') {
          rawMarkdown = `# Welcome to the Application Documentation!
          \nThis documentation provides an overview of the application, guides for various features, and information on system monitoring and setup.
          \n\nUse the sidebar to navigate through different topics.`;
        } else if (filename === '00-how_to.md') {
          rawMarkdown = `# How To Guides
          \nThis section contains step-by-step guides for common tasks.
          \n\n## Creating a New Project
          \n1. Navigate to the 'Projects' section.
          \n2. Click on 'Create New Project'.
          \n3. Fill in the project details and submit.
          \n\n## Reporting a Bug
          \n1. Go to the specific project's 'Bugs' tab.
          \n2. Click 'Report New Bug'.
          \n3. Provide a title, description, version, and criticality.`;
        } else if (filename === '00-monitoring.md') {
            rawMarkdown = `# Monitoring
            \nDetails about application monitoring, logs, and performance metrics.
            \n- Log locations: \`/var/log/app.log\`
            \n- Monitoring dashboard: [link to Grafana/Kibana]`;
        } else if (filename === 'project_setup.md') {
            rawMarkdown = `# Project Setup
            \nInformation on setting up new projects, configuring versions, and managing user access within projects.`;
        } else if (filename === 'bug_tracking.md') {
            rawMarkdown = `# Bug Tracking Process
            \nOverview of how bugs are reported, triaged, assigned, fixed, and verified.
            \n\n**Statuses:**
            \n- Open
            \n- Fix Ready
            \n- Closed`;
        }

        this.currentDocContent = marked.parse(rawMarkdown);
      } catch (e) {
        this.error = e.message || `Failed to fetch documentation content for ${filename}.`;
        this.currentDocContent = '<p>Error loading document. Please try again later.</p>';
        console.error("fetchDocContent error:", e);
      } finally {
        this.isLoading = false;
      }
    }
  }
});
