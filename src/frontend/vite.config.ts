import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths"
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  resolve: {
    alias: {
      // This is the key line that tells Vite what '@' means
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,      
    port: 5173,
    strictPort: true
  }
});