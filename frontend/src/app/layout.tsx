import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-Image & Deepfake Forensics Inspector",
  description:
    "Multi-layered forensic verification workspace combining EXIF/C2PA provenance auditing, Error Level Analysis (ELA), 2D FFT spectral forensics, and Deep Vision Grad-CAM explainability.",
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#060911",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        {/* MANDATORY per dark-mode guidance: declare dark scheme before first paint */}
        <meta name="color-scheme" content="dark" />
      </head>
      <body className="min-h-screen antialiased selection:bg-cyan-400/30 selection:text-cyan-100">
        {children}
      </body>
    </html>
  );
}
