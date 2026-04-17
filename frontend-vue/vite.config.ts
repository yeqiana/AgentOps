import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 聊天接口代理
      "/chat": {
        target: "http://localhost:8011",
        changeOrigin: true,
        ws: true  // 支持 WebSocket（如果后续需要）
      },
      "/assets": {
        target: "http://localhost:8011",
        changeOrigin: true
      },
      // 其他 API 接口代理
      "/api": {
        target: "http://localhost:8011",
        changeOrigin: true
      }
    }
  }
});
