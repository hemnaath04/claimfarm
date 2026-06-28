import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Pin the workspace root to this app so Turbopack doesn't infer a parent
  // directory from stray lockfiles (e.g. ~/package-lock.json). Fixes the
  // "inferred your workspace root" build warning. (WUX-B01)
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
