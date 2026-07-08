"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import {
  ShoppingCart,
  User,
  Menu,
  X,
  Zap,
  Sun,
  LayoutDashboard,
} from "lucide-react";
import { useApp } from "@/providers/AppProvider";

interface NavbarProps {
  cartCount: number;
  onCartClick: () => void;
  onLoginClick: () => void;
  isLoggedIn: boolean;
}

const navLinks = [
  { label: "PV-Anlagen", category: "pv" },
  { label: "Batteriespeicher", category: "battery" },
  { label: "Elektroteile", category: "parts" },
  { label: "Projekte", category: "projects" },
  { label: "Kontakt", category: "contact" },
];

export function Navbar({
  cartCount,
  onCartClick,
  onLoginClick,
  isLoggedIn,
}: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentCategory = searchParams.get("category") ?? "all";

  const handleNavigate = (category: string) => {
    router.push(`/?category=${category}`);
    setMobileOpen(false);
  };

  const handleDashboardClick = () => {
    if (isLoggedIn) {
      router.push("/dashboard");
    } else {
      onLoginClick();
    }
    setMobileOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 bg-primary text-primary-foreground shadow-lg">
      {/* Top bar */}
      <div className="border-b border-white/10 px-4 py-1.5 hidden md:block">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-6 text-xs text-white/70">
            <span className="flex items-center gap-1">
              <Zap size={11} className="text-accent" />
              Über 2.150 erfolgreich installierte Anlagen
            </span>
            <span>Mo–Fr 08:00–17:00 Uhr</span>
            <a href="tel:+493912345678" className="hover:text-accent transition-colors">
              +49 391 234 56 78
            </a>
          </div>
          <div className="flex items-center gap-4 text-xs text-white/70">
            <span>9 Jahre Erfahrung</span>
            <span className="text-accent font-semibold">Kostenlose Beratung</span>
          </div>
        </div>
      </div>

      {/* Main nav */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <Link
          href="/frontend/public"
          className="flex items-center gap-2.5 shrink-0"
          onClick={() => setMobileOpen(false)}
        >
          <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shadow-md">
            <Sun size={18} className="text-primary" />
          </div>
          <div>
            <div
              className="text-white font-black leading-none tracking-wide"
              style={{ fontFamily: "var(--font-display)", fontSize: "1.15rem" }}
            >
              KÖNIG<span className="text-accent">39</span>
            </div>
            <div className="text-white/50 leading-none" style={{ fontSize: "0.6rem" }}>
              PV & Elektro Fachhandel
            </div>
          </div>
        </Link>

        {/* Desktop nav links */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <button
              key={link.category}
              onClick={() => handleNavigate(link.category)}
              className={`px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                currentCategory === link.category
                  ? "bg-accent text-primary"
                  : "text-white/80 hover:text-white hover:bg-white/10"
              }`}
              style={{ fontFamily: "var(--font-display)" }}
            >
              {link.label}
            </button>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleDashboardClick}
            className="hidden md:flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-white/80 hover:text-white hover:bg-white/10 transition-all"
          >
            {isLoggedIn ? (
              <>
                <LayoutDashboard size={15} />
                <span className="font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                  Mein Konto
                </span>
              </>
            ) : (
              <>
                <User size={15} />
                <span className="font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                  Anmelden
                </span>
              </>
            )}
          </button>

          <button
            onClick={onCartClick}
            className="relative p-2.5 rounded-lg bg-accent/20 hover:bg-accent text-white hover:text-primary transition-all"
          >
            <ShoppingCart size={18} />
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-accent text-primary text-xs font-black flex items-center justify-center">
                {cartCount > 9 ? "9+" : cartCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2.5 rounded-lg hover:bg-white/10 text-white"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-white/10 bg-primary px-4 py-3 space-y-1">
          {navLinks.map((link) => (
            <button
              key={link.category}
              onClick={() => handleNavigate(link.category)}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                currentCategory === link.category
                  ? "bg-accent text-primary"
                  : "text-white/80 hover:text-white hover:bg-white/10"
              }`}
              style={{ fontFamily: "var(--font-display)" }}
            >
              {link.label}
            </button>
          ))}
          <button
            onClick={handleDashboardClick}
            className="w-full text-left px-3 py-2.5 rounded-lg text-sm text-white/80 hover:text-white hover:bg-white/10 flex items-center gap-2"
          >
            <User size={15} />
            <span className="font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              {isLoggedIn ? "Mein Konto" : "Anmelden"}
            </span>
          </button>
        </div>
      )}
    </header>
  );
}
