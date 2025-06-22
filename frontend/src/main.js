import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import BaseButton from './components/utils/BaseButton.vue';

const app = createApp(App)

app.use(createPinia())
app.use(router) // Use the router

app.component('BaseButton', BaseButton);

app.mount('#app')
