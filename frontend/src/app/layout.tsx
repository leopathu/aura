import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aura - Agentic Data & Knowledge Platform",
  description: "Secure, open-source agentic data & knowledge platform connecting enterprise databases, documents, and tools with natural language.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-aura-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
