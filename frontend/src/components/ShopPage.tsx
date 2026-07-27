"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ShoppingCart,
  Star,
  ArrowRight,
  CheckCircle,
  Zap,
  Shield,
  Phone,
  ChevronRight,
  Sun,
  Battery,
  Cpu,
  Cable,
  Loader2,
} from "lucide-react";
import { ImageWithFallback } from "@/src/components/figma/ImageWithFallback";
import { fetchCategories, fetchProducts } from "@/src/lib/catalog";
import type { CatalogCategory, CatalogProduct } from "@/src/types/catalog";

const CATEGORY_UI: Record<
  string,
  {
    icon: typeof Sun;
    color: string;
  }
> = {
  pv: { icon: Sun, color: "from-amber-400 to-orange-500" },
  battery: { icon: Battery, color: "from-blue-500 to-cyan-500" },
  parts: { icon: Cpu, color: "from-slate-600 to-slate-800" },
  cables: { icon: Cable, color: "from-emerald-500 to-teal-600" },
};

const BENEFITS = [
  {
    icon: CheckCircle,
    title: "Fachbetrieb seit 2017",
    text: "Zertifizierter Elektroinstallateur mit über 9 Jahren Erfahrung",
  },
  {
    icon: Zap,
    title: "2.150+ Projekte",
    text: "Erfolgreich realisierte Anlagen in der Region Sachsen-Anhalt",
  },
  {
    icon: Shield,
    title: "10 Jahre Garantie",
    text: "Auf alle verbauten Solarmodule und Systemkomponenten",
  },
  {
    icon: Phone,
    title: "Persönliche Beratung",
    text: "Kostenlos und unverbindlich – vor Ort oder telefonisch",
  },
];

interface ShopPageProps {
  onAddToCart: (product: CatalogProduct) => void;
  activeCategory: string;
  onCategoryChange: (cat: string) => void;
  onProductClick: (product: CatalogProduct) => void;
}

export function ShopPage({
  onAddToCart,
  activeCategory,
  onCategoryChange,
  onProductClick,
}: ShopPageProps) {
  const [addedId, setAddedId] = useState<number | null>(null);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [categories, setCategories] = useState<CatalogCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadCatalog() {
      setLoading(true);
      setError(null);
      try {
        const [cats, items] = await Promise.all([
          fetchCategories(),
          fetchProducts(),
        ]);
        if (!cancelled) {
          setCategories(cats);
          setProducts(items);
        }
      } catch {
        if (!cancelled) {
          setError("Katalog konnte nicht geladen werden. Bitte später erneut versuchen.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadCatalog();
    return () => {
      cancelled = true;
    };
  }, []);

  const productCountByCategory = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const product of products) {
      counts[product.category] = (counts[product.category] ?? 0) + 1;
    }
    return counts;
  }, [products]);

  const filtered =
    activeCategory === "all"
      ? products
      : products.filter((p) => p.category === activeCategory);

  const activeCategoryLabel =
    activeCategory === "all"
      ? "Alle Produkte"
      : categories.find((c) => c.slug === activeCategory)?.name ?? "Produkte";

  const handleAdd = (product: CatalogProduct) => {
    onAddToCart(product);
    setAddedId(product.id);
    setTimeout(() => setAddedId(null), 1500);
  };

  return (
    <div className="min-h-screen bg-background">
      <section className="relative overflow-hidden bg-primary" style={{ minHeight: 480 }}>
        <div className="absolute inset-0">
          <ImageWithFallback
            src="https://images.unsplash.com/photo-1776182869767-2ede57640c8a?w=1600&h=700&fit=crop&auto=format"
            alt="Solaranlage auf Hausdach"
            className="w-full h-full object-cover opacity-25"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-primary via-primary/90 to-primary/50" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 py-20 md:py-28 flex flex-col md:flex-row items-center gap-12">
          <div className="flex-1 text-white">
            <div className="inline-flex items-center gap-2 bg-accent/20 border border-accent/30 rounded px-3 py-1 mb-6">
              <Sun size={13} className="text-accent" />
              <span className="text-accent text-xs font-semibold tracking-wider uppercase">
                Ihr Solar-Fachbetrieb
              </span>
            </div>
            <h1
              className="text-white mb-5 leading-tight"
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(2rem, 5vw, 3.25rem)",
                fontWeight: 800,
              }}
            >
              Solarenergie & Elektrotechnik
              <br />
              <span className="text-accent">direkt vom Fachbetrieb</span>
            </h1>
            <p
              className="text-white/70 mb-8 max-w-xl leading-relaxed"
              style={{ fontSize: "1.05rem" }}
            >
              Hochwertige PV-Anlagen, Batteriespeicher und Elektroteile — kompetent
              beraten, schnell geliefert, professionell installiert.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => onCategoryChange("pv")}
                className="px-6 py-3 bg-accent text-primary font-bold rounded hover:bg-accent/90 transition-colors flex items-center gap-2"
              >
                PV-Anlagen entdecken <ArrowRight size={16} />
              </button>
              <button
                onClick={() => onCategoryChange("all")}
                className="px-6 py-3 border border-white/30 text-white font-medium rounded hover:bg-white/10 transition-colors"
              >
                Gesamtkatalog
              </button>
            </div>
          </div>

          <div className="hidden md:grid grid-cols-2 gap-px bg-white/10 rounded-xl overflow-hidden shrink-0 w-64">
            {[
              { value: "2.150+", label: "Projekte" },
              { value: "9 Jahre", label: "Erfahrung" },
              { value: "10 J.", label: "Garantie" },
              { value: "100%", label: "Kundenzufriedenheit" },
            ].map((s) => (
              <div key={s.label} className="bg-white/5 px-5 py-4 text-center backdrop-blur-sm">
                <div
                  className="text-accent font-bold mb-0.5"
                  style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem" }}
                >
                  {s.value}
                </div>
                <div className="text-white/60 text-xs">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex items-end justify-between mb-7">
          <div>
            <h2
              className="text-foreground mb-1"
              style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}
            >
              Produktkategorien
            </h2>
            <p className="text-muted-foreground text-sm">
              Finden Sie die richtigen Komponenten für Ihr Projekt
            </p>
          </div>
          <button
            onClick={() => onCategoryChange("all")}
            className="text-sm text-accent font-semibold flex items-center gap-1 hover:gap-2 transition-all"
          >
            Alle anzeigen <ChevronRight size={15} />
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {categories.map((cat) => {
            const ui = CATEGORY_UI[cat.slug] ?? CATEGORY_UI.parts;
            const Icon = ui.icon;
            const isActive = activeCategory === cat.slug;
            const count = productCountByCategory[cat.slug] ?? 0;
            return (
              <button
                key={cat.id}
                onClick={() => onCategoryChange(cat.slug)}
                className={`relative overflow-hidden rounded-xl text-left group border-2 transition-all duration-200 ${
                  isActive ? "border-accent shadow-lg" : "border-transparent hover:border-accent/30"
                }`}
                style={{ minHeight: 160 }}
              >
                <ImageWithFallback
                  src={cat.image_url}
                  alt={cat.name}
                  className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className={`absolute inset-0 bg-gradient-to-t ${ui.color} opacity-80`} />
                {isActive && <div className="absolute inset-0 ring-2 ring-accent rounded-xl" />}
                <div
                  className="relative p-4 flex flex-col h-full justify-between text-white"
                  style={{ minHeight: 160 }}
                >
                  <Icon size={22} className="opacity-90" />
                  <div>
                    <div
                      className="font-bold leading-tight mb-0.5"
                      style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem" }}
                    >
                      {cat.name}
                    </div>
                    <div className="text-white/70 text-xs mb-1">{cat.sublabel}</div>
                    <div className="text-white/60 text-xs">{count} Artikel</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 pb-12">
        <div className="flex items-end justify-between mb-6">
          <h2
            className="text-foreground"
            style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}
          >
            {activeCategoryLabel}
          </h2>
          <span className="text-muted-foreground text-sm">{filtered.length} Artikel</span>
        </div>

        {loading && (
          <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground text-sm">
            <Loader2 size={18} className="animate-spin" />
            Katalog wird geladen…
          </div>
        )}

        {!loading && error && (
          <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((product) => (
              <div
                key={product.id}
                className="bg-card border border-border rounded-xl overflow-hidden flex flex-col hover:shadow-md transition-shadow group cursor-pointer"
                onClick={() => onProductClick(product)}
              >
                <div className="relative overflow-hidden bg-muted" style={{ height: 190 }}>
                  <ImageWithFallback
                    src={product.image}
                    alt={product.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  {product.badge && (
                    <span className="absolute top-3 left-3 px-2.5 py-1 bg-accent text-primary text-xs font-bold rounded">
                      {product.badge}
                    </span>
                  )}
                  {product.watt && (
                    <span className="absolute bottom-3 right-3 px-2 py-0.5 bg-primary/80 text-white text-xs rounded backdrop-blur-sm">
                      {product.watt}
                    </span>
                  )}
                </div>
                <div className="p-4 flex flex-col flex-1">
                  <h3
                    className="text-foreground mb-1 leading-snug"
                    style={{
                      fontFamily: "var(--font-display)",
                      fontWeight: 600,
                      fontSize: "0.9rem",
                    }}
                  >
                    {product.name}
                  </h3>
                  <p className="text-muted-foreground text-xs mb-3 leading-relaxed flex-1">
                    {product.description}
                  </p>
                  <div className="flex items-center gap-1.5 mb-3">
                    <div className="flex">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star
                          key={i}
                          size={11}
                          className={
                            i < Math.floor(product.rating)
                              ? "text-accent fill-accent"
                              : "text-muted-foreground"
                          }
                        />
                      ))}
                    </div>
                    <span className="text-muted-foreground text-xs">({product.reviews})</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <span
                        className="text-foreground font-bold"
                        style={{ fontFamily: "var(--font-display)", fontSize: "1.15rem" }}
                      >
                        {product.price.toLocaleString("de-DE", {
                          style: "currency",
                          currency: "EUR",
                        })}
                      </span>
                      {product.originalPrice != null && (
                        <span className="text-muted-foreground text-xs line-through ml-2">
                          {product.originalPrice.toLocaleString("de-DE", {
                            style: "currency",
                            currency: "EUR",
                          })}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAdd(product);
                      }}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded text-xs font-semibold transition-all duration-200 ${
                        addedId === product.id
                          ? "bg-green-500 text-white"
                          : "bg-primary text-primary-foreground hover:bg-primary/90"
                      }`}
                    >
                      <ShoppingCart size={13} />
                      {addedId === product.id ? "Hinzugefügt!" : "In den Korb"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="bg-primary py-14">
        <div className="max-w-7xl mx-auto px-4">
          <h2
            className="text-white text-center mb-10"
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "1.6rem",
            }}
          >
            Warum <span className="text-accent">König 39</span>?
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {BENEFITS.map((b) => {
              const Icon = b.icon;
              return (
                <div
                  key={b.title}
                  className="text-center p-6 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                >
                  <div className="w-12 h-12 rounded-lg bg-accent/20 flex items-center justify-center mx-auto mb-4">
                    <Icon size={22} className="text-accent" />
                  </div>
                  <h3
                    className="text-white mb-2"
                    style={{
                      fontFamily: "var(--font-display)",
                      fontWeight: 600,
                      fontSize: "0.95rem",
                    }}
                  >
                    {b.title}
                  </h3>
                  <p className="text-white/60 text-xs leading-relaxed">{b.text}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="bg-accent py-10">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h2
              className="text-primary mb-1"
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: 800,
                fontSize: "1.4rem",
              }}
            >
              Kostenlose Beratung vereinbaren
            </h2>
            <p className="text-primary/70 text-sm">
              Wir planen Ihre individuelle PV-Anlage — unverbindlich und vor Ort.
            </p>
          </div>
          <div className="flex gap-3 shrink-0">
            <a
              href="tel:+493912345678"
              className="px-6 py-3 bg-primary text-white font-bold rounded flex items-center gap-2 hover:bg-primary/90 transition-colors text-sm"
            >
              <Phone size={15} /> Jetzt anrufen
            </a>
            <button className="px-6 py-3 border-2 border-primary/30 text-primary font-semibold rounded hover:border-primary transition-colors text-sm">
              Online anfragen
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
