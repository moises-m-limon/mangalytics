import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "mangalytics - research made fun",
  description: "research papers as manga, delivered to your inbox",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
