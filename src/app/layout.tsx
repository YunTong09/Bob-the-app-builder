import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rage-to-Reply",
  description: "Turn a private vent into a professional reply.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
