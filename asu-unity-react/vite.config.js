import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { execSync } from 'child_process'

const commitHash = execSync('git rev-parse --short HEAD').toString().trim()
const commitMessage = execSync('git log -1 --pretty=%s').toString().trim()

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    __COMMIT_HASH__: JSON.stringify(commitHash),
    __COMMIT_MESSAGE__: JSON.stringify(commitMessage),
  },
})
