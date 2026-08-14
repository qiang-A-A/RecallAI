// vite.config.ts
import { defineConfig } from "file:///C:/Users/%E6%9E%97%E5%90%AF%E6%89%AC/WorkBuddy/2026-08-10-15-59-14/recall-ai-app/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///C:/Users/%E6%9E%97%E5%90%AF%E6%89%AC/WorkBuddy/2026-08-10-15-59-14/recall-ai-app/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { viteSingleFile } from "file:///C:/Users/%E6%9E%97%E5%90%AF%E6%89%AC/WorkBuddy/2026-08-10-15-59-14/recall-ai-app/frontend/node_modules/vite-plugin-singlefile/dist/esm/index.js";
import path from "node:path";
var __vite_injected_original_dirname = "C:\\Users\\\u6797\u542F\u626C\\WorkBuddy\\2026-08-10-15-59-14\\recall-ai-app\\frontend";
var vite_config_default = defineConfig(({ mode }) => ({
  plugins: [vue(), viteSingleFile()],
  resolve: {
    alias: { "@": path.resolve(__vite_injected_original_dirname, "src") }
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true }
    }
  },
  define: {
    // 构建静态演示版时 VITE_OFFLINE=true,注入离线模拟数据开关
    __OFFLINE__: JSON.stringify(mode === "offline")
  }
}));
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxcdTY3OTdcdTU0MkZcdTYyNkNcXFxcV29ya0J1ZGR5XFxcXDIwMjYtMDgtMTAtMTUtNTktMTRcXFxccmVjYWxsLWFpLWFwcFxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcVXNlcnNcXFxcXHU2Nzk3XHU1NDJGXHU2MjZDXFxcXFdvcmtCdWRkeVxcXFwyMDI2LTA4LTEwLTE1LTU5LTE0XFxcXHJlY2FsbC1haS1hcHBcXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L1VzZXJzLyVFNiU5RSU5NyVFNSU5MCVBRiVFNiU4OSVBQy9Xb3JrQnVkZHkvMjAyNi0wOC0xMC0xNS01OS0xNC9yZWNhbGwtYWktYXBwL2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcbmltcG9ydCB2dWUgZnJvbSAnQHZpdGVqcy9wbHVnaW4tdnVlJ1xuaW1wb3J0IHsgdml0ZVNpbmdsZUZpbGUgfSBmcm9tICd2aXRlLXBsdWdpbi1zaW5nbGVmaWxlJ1xuaW1wb3J0IHBhdGggZnJvbSAnbm9kZTpwYXRoJ1xuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoKHsgbW9kZSB9KSA9PiAoe1xuICBwbHVnaW5zOiBbdnVlKCksIHZpdGVTaW5nbGVGaWxlKCldLFxuICByZXNvbHZlOiB7XG4gICAgYWxpYXM6IHsgJ0AnOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCAnc3JjJykgfSxcbiAgfSxcbiAgc2VydmVyOiB7XG4gICAgcG9ydDogNTE3MyxcbiAgICBwcm94eToge1xuICAgICAgJy9hcGknOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODAwMCcsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgIH0sXG4gIH0sXG4gIGRlZmluZToge1xuICAgIC8vIFx1Njc4NFx1NUVGQVx1OTc1OVx1NjAwMVx1NkYxNFx1NzkzQVx1NzI0OFx1NjVGNiBWSVRFX09GRkxJTkU9dHJ1ZSxcdTZDRThcdTUxNjVcdTc5QkJcdTdFQkZcdTZBMjFcdTYyREZcdTY1NzBcdTYzNkVcdTVGMDBcdTUxNzNcbiAgICBfX09GRkxJTkVfXzogSlNPTi5zdHJpbmdpZnkobW9kZSA9PT0gJ29mZmxpbmUnKSxcbiAgfSxcbn0pKVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUEyWixTQUFTLG9CQUFvQjtBQUN4YixPQUFPLFNBQVM7QUFDaEIsU0FBUyxzQkFBc0I7QUFDL0IsT0FBTyxVQUFVO0FBSGpCLElBQU0sbUNBQW1DO0FBS3pDLElBQU8sc0JBQVEsYUFBYSxDQUFDLEVBQUUsS0FBSyxPQUFPO0FBQUEsRUFDekMsU0FBUyxDQUFDLElBQUksR0FBRyxlQUFlLENBQUM7QUFBQSxFQUNqQyxTQUFTO0FBQUEsSUFDUCxPQUFPLEVBQUUsS0FBSyxLQUFLLFFBQVEsa0NBQVcsS0FBSyxFQUFFO0FBQUEsRUFDL0M7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLFFBQVEsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQSxJQUNoRTtBQUFBLEVBQ0Y7QUFBQSxFQUNBLFFBQVE7QUFBQTtBQUFBLElBRU4sYUFBYSxLQUFLLFVBQVUsU0FBUyxTQUFTO0FBQUEsRUFDaEQ7QUFDRixFQUFFOyIsCiAgIm5hbWVzIjogW10KfQo=
