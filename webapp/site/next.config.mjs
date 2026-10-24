/** @type {import('next').NextConfig} */
import { fileURLToPath } from "node:url";
import path from "node:path";

const nextConfig = {
  outputFileTracingRoot: path.dirname(fileURLToPath(import.meta.url)),
  // the Ask route reads data/*.json from disk at runtime
  outputFileTracingIncludes: { "/api/ask": ["./data/**/*"] },
  // local test builds go to their own folder so they don't break a running dev server (NEXT_DIST_DIR=.next-test)
  ...(process.env.NEXT_DIST_DIR ? { distDir: process.env.NEXT_DIST_DIR } : {}),
};
export default nextConfig;
