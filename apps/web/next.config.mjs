import path from "path";
import { fileURLToPath } from "url";

// This directory is always `apps/web` (where this config lives). Stops Turbopack from guessing
// a parent workspace root when multiple `package-lock.json` files exist (e.g. under the user profile).
const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: __dirname,
  },

  // Standalone output matches `infra/docker/Dockerfile.web` (`node server.js`).
  output: "standalone",

  /**
   * When the browser calls same-origin `/api/v1/*`, forward to FastAPI so we avoid CORS.
   * - Local Next dev: default target http://127.0.0.1:8000
   * - Docker web image: pass API_PROXY_TARGET=http://api:8000 at build time
   */
  async redirects() {
    return [
      { source: "/Dashboard", destination: "/dashboard", permanent: false },
    ];
  },

  async rewrites() {
    const target = (process.env.API_PROXY_TARGET || "http://127.0.0.1:8000").replace(/\/$/, "");
    return [
      {
        source: "/api/v1/:path*",
        destination: `${target}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
