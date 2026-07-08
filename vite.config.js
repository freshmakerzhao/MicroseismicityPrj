import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"

function resolve(url) {
  return path.resolve(__dirname, url)
}

export default defineConfig({
  base: "./",
  assetsInclude: [
    "**/*.glb",
    "**/*.gltf",
    "**/*.fbx",
    "**/*.hdr",
    "**/*.json",
    "**/*.mp4",
    "**/*.mov",
  ],
  resolve: {
    alias: {
      "@": resolve("./src"),
      "~@": resolve("./src"),
    },
    extensions: [".mjs", ".js", ".jsx", ".json", ".vue"],
  },
  server: {
    host: "127.0.0.1",
    port: 8084,
  },
  build: {
    minify: "esbuild",
    target: "es2015",
    cssTarget: "chrome80",
    outDir: "dist",
    reportCompressedSize: false,
    chunkSizeWarningLimit: 2400,
  },
  plugins: [vue()],
})
