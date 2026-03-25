import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";
import { existsSync, readdirSync } from "fs";
import { resolve } from "path";

const islandsDir = resolve(__dirname, "src/islands");
const entries = Object.fromEntries(
  readdirSync(islandsDir)
    .filter((name) => existsSync(resolve(islandsDir, name, "index.js")))
    .map((name) => [name, resolve(islandsDir, name, "index.js")])
);

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: "../backend/app/static/dist/islands",
    emptyOutDir: true,
    rollupOptions: {
      input: entries,
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "chunks/[name]-[hash].js",
      },
    },
  },
});
