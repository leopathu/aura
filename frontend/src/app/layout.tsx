import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aura - Augmented Understanding & Retrieval Assistant",
  description: "A modern full-stack application built with Next.js and FastAPI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
