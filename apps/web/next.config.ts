import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Allow local SVG and PNG assets — all served from /public
    unoptimized: false,
  },
  async rewrites() {
    // Proxy /api/* → API server so frontend never needs CORS in dev
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
