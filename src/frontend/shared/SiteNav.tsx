"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const pages = [
  { href: "/", label: "Workspace" },
  { href: "/assistant", label: "Assistant" },
];

export default function SiteNav() {
  const pathname = usePathname();

  return (
    <nav className="site-nav" aria-label="Main navigation">
      <div className="site-nav-inner">
        {pages.map(({ href, label }) => (
          <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}>
            {label}
          </Link>
        ))}
        <div className="theme-control">
          <label htmlFor="site-theme">Theme</label>
          <select id="site-theme" defaultValue="system" onChange={(event) => {
            const theme = event.target.value;
            if (theme === "system") {
              delete document.documentElement.dataset.theme;
            } else {
              document.documentElement.dataset.theme = theme;
            }
          }}>
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>
    </nav>
  );
}
