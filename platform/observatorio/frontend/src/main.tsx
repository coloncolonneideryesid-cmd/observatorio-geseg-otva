import { createRoot } from 'react-dom/client'
import '@fontsource/montserrat/600.css'
import '@fontsource/montserrat/700.css'
import '@fontsource/roboto/400.css'
import '@fontsource/roboto/500.css'
import 'leaflet/dist/leaflet.css'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(<App />)
