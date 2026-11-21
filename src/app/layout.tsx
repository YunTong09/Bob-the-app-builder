import type { Metadata } from "next";
import SiteNav from "@/frontend/shared/SiteNav";
import { fontSizeInitScript } from "@/frontend/features/preferences/fontSize";
import "@/frontend/styles/globals.css";
import "@/frontend/styles/pixel-workspace.css";

export const metadata: Metadata = {
  title: "Rage-to-Reply",
  description: "Turn a private vent into a professional reply.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: fontSizeInitScript }} />
      </head>
      <body>
        <SiteNav />
        {children}
      </body>
    </html>
  );
}
