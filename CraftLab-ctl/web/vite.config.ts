import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, "../.."), "");
  const ctlHost = env.CRAFTLAB_CTL_HOST || process.env.CRAFTLAB_CTL_HOST || "127.0.0.1";
  const ctlPort = env.CRAFTLAB_CTL_PORT || process.env.CRAFTLAB_CTL_PORT || "8443";

  return {
    plugins: [react()],
    build: {
      outDir: "dist",
      emptyOutDir: true,
    },
    server: {
      port: 5174,
      proxy: {
        "/api": {
          target: `http://${ctlHost}:${ctlPort}`,
          changeOrigin: true,
          ws: true,
        },
      },
    },
  };
});
