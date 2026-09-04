import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'
import '@vuepic/vue-datepicker/dist/main.css'

import './assets/main.css'

const app = createApp(App)

app.use(createPinia())

useThemeStore().init()

app.use(router)

app.mount('#app')