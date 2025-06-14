<template>
  <div class="documentation-view">
    <aside class="doc-sidebar">
      <h3>Documentation Topics</h3>
      <div v-if="docStore.isLoading && docStore.docFiles.length === 0 && !docStore.error" class="loading">Loading topics...</div>
      <ul v-if="docStore.docFiles.length > 0">
        <li v-for="docFile in docStore.docFiles" :key="docFile.name">
          <a href="#" @click.prevent="loadDocument(docFile.name)"
             :class="{ active: docStore.currentDocName === docFile.name }">
            {{ docFile.title }}
          </a>
        </li>
      </ul>
      <div v-if="docStore.error && docStore.docFiles.length === 0" class="error-message">
        Failed to load topics: {{ docStore.error }}
      </div>
    </aside>
    <main class="doc-content">
      <div v-if="docStore.isLoading && !docStore.currentDocContent" class="loading">Loading document...</div>
      <div v-if="docStore.error && docStore.currentDocName" class="error-message"> <!-- Show error if specific doc failed -->
        Failed to load document '{{docStore.currentDocName}}': {{ docStore.error }}
      </div>
      <!-- Use v-html carefully. Ensure markdown source is trusted or sanitized. -->
      <div v-if="docStore.currentDocContent" v-html="docStore.currentDocContent" class="markdown-body"></div>
      <div v-if="!docStore.isLoading && !docStore.currentDocContent && !docStore.currentDocName && !docStore.error" class="no-data">
        Select a document from the sidebar to view its content.
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, computed } from 'vue';
import { useDocumentationStore } from '../stores/documentationStore';
import { useRoute, useRouter } from 'vue-router';

const docStore = useDocumentationStore();
const route = useRoute();
const router = useRouter();

// currentDocName is now primarily managed by the store to reflect what's loaded/loading
// const currentDocName = ref(''); // Replaced by docStore.currentDocName

const loadDocument = (filename) => {
  // Update URL query parameter
  if (route.query.page !== filename) {
    router.push({ query: { page: filename } });
  }
  // Fetch content (store action will set currentDocName)
  docStore.fetchDocContent(filename);
};

onMounted(() => {
  docStore.fetchDocFiles().then(() => {
    const pageFromQuery = route.query.page;
    if (pageFromQuery && docStore.docFiles.some(f => f.name === pageFromQuery)) {
      loadDocument(pageFromQuery);
    } else if (docStore.docFiles.length > 0 && !docStore.currentDocName) {
      // Load default document (e.g., index.md) if no specific page is selected and none loaded
      loadDocument(docStore.docFiles[0].name);
    }
  });
});

// Watch for direct URL changes to the query parameter
watch(() => route.query.page, (newPage) => {
    if (newPage && newPage !== docStore.currentDocName) { // Check against store's current doc
        if (docStore.docFiles.length === 0) {
            docStore.fetchDocFiles().then(() => { // Ensure files are loaded before trying to load content
                if (docStore.docFiles.some(f => f.name === newPage)) {
                    loadDocument(newPage);
                } else if (docStore.docFiles.length > 0) { // Fallback if specific page not found
                    loadDocument(docStore.docFiles[0].name);
                }
            });
        } else if (docStore.docFiles.some(f => f.name === newPage)) {
             loadDocument(newPage);
        } else if (docStore.docFiles.length > 0) { // Fallback if specific page not found
             loadDocument(docStore.docFiles[0].name);
        }
    } else if (!newPage && docStore.docFiles.length > 0 && !docStore.currentDocName) {
        // If query is removed and no doc is loaded, load the first one.
        loadDocument(docStore.docFiles[0].name);
    }
});

</script>

<style scoped>
.documentation-view {
  display: flex;
  height: calc(100vh - 120px); /* Adjust based on header/footer height from Layout.vue */
  background-color: #fff;
  border-top: 1px solid #ddd;
}
.doc-sidebar {
  width: 280px; /* Slightly wider sidebar */
  padding: 20px;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  background-color: #f7f9fa; /* Lighter sidebar background */
}
.doc-sidebar h3 {
  margin-top: 0;
  font-size: 1.3em;
  color: #2c3e50;
  margin-bottom: 15px;
}
.doc-sidebar ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}
.doc-sidebar li a {
  display: block;
  padding: 10px 15px; /* More padding */
  text-decoration: none;
  color: #007bff;
  border-radius: 5px;
  margin-bottom: 6px;
  transition: background-color 0.2s ease, color 0.2s ease;
  font-size: 0.95em;
}
.doc-sidebar li a:hover {
  background-color: #e9ecef;
  color: #0056b3;
}
.doc-sidebar li a.active {
  background-color: #007bff;
  color: white;
  font-weight: 600;
}
.doc-content {
  flex-grow: 1;
  padding: 25px 30px; /* More padding in content area */
  overflow-y: auto;
}
.markdown-body {
  line-height: 1.7;
  color: #333;
}
/* Using :deep selector for styles applied to v-html content */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin-top: 1.8em;
  margin-bottom: 0.8em;
  color: #2c3e50;
  font-weight: 600;
}
.markdown-body :deep(h1) { font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em;}
.markdown-body :deep(h2) { font-size: 1.75em; border-bottom: 1px solid #eee; padding-bottom: 0.3em;}
.markdown-body :deep(h3) { font-size: 1.5em; }
.markdown-body :deep(h4) { font-size: 1.25em; }

.markdown-body :deep(p) { margin-bottom: 1.2em; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin-bottom: 1.2em; padding-left: 25px; }
.markdown-body :deep(li) { margin-bottom: 0.5em; }

.markdown-body :deep(code) {
  background-color: #eef1f3; /* Lighter code background */
  padding: 0.2em 0.5em;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  font-size: 0.9em;
  color: #2d3748; /* Darker code text */
}
.markdown-body :deep(pre) {
  background-color: #2d3748; /* Darker background for code blocks */
  color: #e2e8f0; /* Lighter text for code blocks */
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 1.2em;
}
.markdown-body :deep(pre code) {
  padding: 0;
  background-color: transparent;
  color: inherit; /* Inherit color from pre */
  font-size: 0.9em;
}
.markdown-body :deep(a) {
  color: #007bff;
  text-decoration: none;
}
.markdown-body :deep(a:hover) {
  text-decoration: underline;
}
.markdown-body :deep(table) {
    border-collapse: collapse;
    width: auto; /* Or 100% if you want full width tables */
    margin-bottom: 1.5em;
    box-shadow: 0 0 5px rgba(0,0,0,0.05);
}
.markdown-body :deep(th), .markdown-body :deep(td) {
    border: 1px solid #dfe2e5; /* Lighter borders */
    padding: 10px 12px; /* More padding in cells */
    text-align: left;
}
.markdown-body :deep(th) {
    background-color: #f6f8fa; /* Lighter header for tables */
    font-weight: 600;
}
.markdown-body :deep(blockquote) {
    border-left: 4px solid #007bff;
    padding-left: 1em;
    margin-left: 0;
    color: #5a6268;
    font-style: italic;
}
.loading, .error-message, .no-data {
  text-align: center;
  padding: 30px;
  font-size: 1.1em;
  color: #6c757d;
}
.error-message { color: #dc3545; }
</style>
