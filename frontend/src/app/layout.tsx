/**
 * Root layout component
 */
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PDF Parser",
  description: "Convert PDFs to Markdown with AI-powered summaries",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
