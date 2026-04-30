import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'


export default defineConfig({
  plugins: [react()],
  server: {
    host: true,                    // ← expõe para a rede externa
    allowedHosts: [
      'multiradial-thu-chuffily.ngrok-free.dev'
    ]
  }
})