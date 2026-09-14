import { defineConfig, viteCssLayerPlugin } from '@vben/vite-config';

import ElementPlus from 'unplugin-element-plus/vite';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      plugins: [
        // element-plus 的 css 包进 @layer el，使 Tailwind 工具类可覆盖组件样式
        viteCssLayerPlugin({ layerName: 'el', packageName: 'element-plus' }),
        ElementPlus({ format: 'esm' }),
      ],
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            // 浏览器 /api/* → FastAPI /api/v1/*
            rewrite: (path) => path.replace(/^\/api/, '/api/v1'),
            target: 'http://127.0.0.1:8000',
            // Keep SSE /chat/stream open; avoid premature proxy timeouts.
            timeout: 0,
            proxyTimeout: 0,
            ws: true,
            configure: (proxy) => {
              proxy.on('proxyRes', (proxyRes, _req, res) => {
                const ct = String(proxyRes.headers['content-type'] || '');
                if (ct.includes('text/event-stream')) {
                  // Discourage intermediary buffering for streaming replies.
                  res.setHeader('Cache-Control', 'no-cache, no-transform');
                  res.setHeader('X-Accel-Buffering', 'no');
                  res.setHeader('Connection', 'keep-alive');
                }
              });
            },
          },
        },
      },
    },
  };
});
