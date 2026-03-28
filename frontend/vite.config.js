import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

function asWsTarget(apiTarget) {
  try {
    const parsed = new URL(apiTarget)
    parsed.protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:'
    return parsed.toString().replace(/\/$/, '')
  } catch {
    return 'ws://127.0.0.1:8000'
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_PROXY_API_TARGET || 'http://127.0.0.1:8000'
  const wsTarget = env.VITE_PROXY_WS_TARGET || asWsTarget(apiTarget)
  const disableProxy = String(env.VITE_DISABLE_PROXY || '').toLowerCase() === 'true'

  return {
    plugins: [react(), tailwindcss()],
    server: disableProxy
      ? {}
      : {
          proxy: {
            '/api': {
              target: apiTarget,
              changeOrigin: true,
            },
            '/ws': {
              target: wsTarget,
              ws: true,
              changeOrigin: true,
            },
          },
        },
  }
})
