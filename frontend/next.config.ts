import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'reducto.ai',
      },
      {
        protocol: 'https',
        hostname: 'firecrawl.dev',
      },
      {
        protocol: 'https',
        hostname: 'lovable.dev',
      },
      {
        protocol: 'https',
        hostname: 'resend.com',
      },
    ],
  },
};

export default nextConfig;
