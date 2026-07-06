import './assets/main.css'
import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
import iconUrl        from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl  from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl      from 'leaflet/dist/images/marker-shadow.png'

// Fix Leaflet default marker icons broken by Vite asset hashing
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl, iconRetinaUrl, shadowUrl })

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')
