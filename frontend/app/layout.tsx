import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Readerike",
  description: "Video transcription powered by Whisper",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">Readerike</span>
          <span className="text-xs text-gray-400 font-mono">video → transcript</span>
        </nav>
        <main className="max-w-4xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
