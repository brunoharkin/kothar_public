import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    port: 5180,
    host: true,
    proxy: {
      // Rotas específicas PRIMEIRO (Vite pega a primeira match)
      '/api/auth': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
      '/api/cbm': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/skills': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/orchestrate': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/sessions': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/traces': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/ollama': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/rag-metrics': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/rag-tracker': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/cofre': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/locks': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/dashboard': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/inspector': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/heatmaps': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/usage': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/evolucao': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:9749',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.setHeader('Origin', 'http://localhost:9749');
          });
        }
      },
      '/rpc': {
        target: 'http://localhost:9749',
        changeOrigin: true,
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.setHeader('Origin', 'http://localhost:9749');
          });
          proxy.on('proxyReqWs', (proxyReq, req, socket, options, head) => {
            proxyReq.setHeader('Origin', 'http://localhost:9749');
          });
        }
      },
      '/cbm-ui': {
        target: 'http://localhost:9749',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/cbm-ui/, ''),
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            proxyReq.setHeader('Origin', 'http://localhost:9749');
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            delete proxyRes.headers['content-security-policy'];
            delete proxyRes.headers['x-frame-options'];
          });
        }
      },
      '/assets': {
        target: 'http://localhost:9749',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            proxyReq.setHeader('Origin', 'http://localhost:9749');
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            delete proxyRes.headers['content-security-policy'];
            delete proxyRes.headers['x-frame-options'];
          });
        }
      }
    },
  },
});
