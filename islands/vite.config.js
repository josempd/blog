import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";
import { readdirSync } from "fs";
import { resolve } from "path";

const entries = {};
for (const file of readdirSync("src")) {
  if (file.endsWith(".js")) {
    entries[file.replace(".js", "")] = resolve("src", file);
  }
}

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: "../backend/app/static/dist/islands",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: entries,
      output: {
        entryFileNames: "[name]-[hash].js",
        chunkFileNames: "chunks/[name]-[hash].js",
      },
    },
  },
});
