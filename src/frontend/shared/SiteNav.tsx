"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
const pages = [
  { href: "/", label: "Reply workspace", icon: "▤" },
  { href: "/assistant", label: "How it works", icon: "▧" },
];
export default function SiteNav() {
  const pathname = usePathname();
  return (
    <nav className="site-nav" aria-label="Main navigation">
      <div className="site-nav-inner">
        <Link href="/" className="site-brand" aria-label="Rage-to-Reply home">
          <span className="pixel-brand" aria-hidden="true">
            r<span>r</span>
          </span>
          <span>
            rage<span className="brand-to">to</span>reply
            <span className="brand-period">.</span>
          </span>
        </Link>
        <div className="nav-caption">YOUR WORKSPACE</div>
        {pages.map((p) => (
          <Link
            key={p.href}
            href={p.href}
            aria-current={pathname === p.href ? "page" : undefined}
          >
            <span aria-hidden="true" className="nav-icon">
              {p.icon}
            </span>
            {p.label}
          </Link>
        ))}
        <div className="nav-bottom">
          <span className="nav-motto">
            A cooler head.
            <br />A stronger reply.
          </span>
          <p>Your words. Your decision.</p>
          <label className="theme-control">
            Appearance
            <select
              aria-label="Appearance"
              defaultValue="dark"
              onChange={(e) => {
                document.documentElement.dataset.theme = e.target.value;
              }}
            >
              <option value="dark">Midnight</option>
              <option value="light">Daylight</option>
            </select>
          </label>
        </div>
      </div>
    </nav>
  );
}
