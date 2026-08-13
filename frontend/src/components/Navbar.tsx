import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/catalog", label: "Catalog" },
  { href: "/modules", label: "Modules" },
];

export default function Navbar() {
  return (
    <nav className="border-b border-slate-200 bg-white px-6 py-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <span className="text-lg font-semibold text-slate-900">
          AI Cloud Self-Service
        </span>
        <div className="flex gap-6">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="text-sm text-slate-600 hover:text-slate-900">
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
