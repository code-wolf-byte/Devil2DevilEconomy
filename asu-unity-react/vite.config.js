import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { execSync } from 'child_process'

function tryExec(command) {
  try {
    return execSync(command, { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()
  } catch {
    return ''
  }
}

function resolveCommitHash() {
  const envHash = process.env.VITE_COMMIT_HASH || process.env.GITHUB_SHA
  if (envHash) return envHash.slice(0, 7)
  return tryExec('git rev-parse --short HEAD') || 'unknown'
}

function resolveCommitMessage() {
  const envMessage = process.env.VITE_COMMIT_MESSAGE || process.env.GITHUB_COMMIT_MESSAGE
  if (envMessage) return envMessage
  return tryExec('git log -1 --pretty=%s') || 'Unavailable'
}

const commitHash = resolveCommitHash()
const commitMessage = resolveCommitMessage()

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    __COMMIT_HASH__: JSON.stringify(commitHash),
    __COMMIT_MESSAGE__: JSON.stringify(commitMessage),
  },
})
