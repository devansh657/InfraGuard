import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom"],
          charts: ["recharts"],
          motion: ["framer-motion"],
          icons: ["lucide-react"]
        }
      }
    }
  },
  server: {
    port: 5173,
    host: "127.0.0.1"
  }
});
