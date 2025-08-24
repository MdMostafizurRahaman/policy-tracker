import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: 'export', // Comment out for development, uncomment for production build
  trailingSlash: false,
  poweredByHeader: false,
  reactStrictMode: false,
  images: {
    unoptimized: true
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  },
  serverExternalPackages: [],
};

export default nextConfig;
