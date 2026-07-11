import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base '/' by default; set VITE_BASE=/repo-name/ when deploying to a GitHub
// Pages project site so asset URLs resolve under the repo subpath.
export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [react()],
  build: { outDir: "dist", sourcemap: false },
});
