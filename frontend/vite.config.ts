import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [
      vue(),
      AutoImport({
        resolvers: [ElementPlusResolver()],
        imports: ['vue', 'vue-router', 'pinia'],
        dts: 'src/auto-imports.d.ts',
      }),
      Components({
        resolvers: [ElementPlusResolver()],
        dts: 'src/components.d.ts',
      }),
    ],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    server: {
      port: 37201,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:38204',
          changeOrigin: true,
        },
      },
    },
    // 生产构建配置
    build: {
      outDir: 'dist',
    },
    // 预览服务器配置（用于本地预览生产构建）
    preview: {
      port: 37201,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:38204',
          changeOrigin: true,
        },
      },
    },
  }
})
