import type { NextConfig } from "next";

const API_UPSTREAM = process.env.BACKEND_UPSTREAM ?? "http://127.0.0.1:8005";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_UPSTREAM}/api/:path*`,
      },
      {
        source: "/media/:path*",
        destination: `${API_UPSTREAM}/media/:path*`,
      },
      {
        source: "/docs",
        destination: `${API_UPSTREAM}/docs`,
      },
      {
        source: "/openapi.json",
        destination: `${API_UPSTREAM}/openapi.json`,
      },
    ];
  },
};

export default nextConfig;