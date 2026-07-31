import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GAGF Governance Assessment Console",
  description: "Evidence-governed assessment and audit console"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
