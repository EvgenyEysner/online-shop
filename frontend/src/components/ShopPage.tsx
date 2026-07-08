"use client";
import { useState } from "react";
import { ShoppingCart, Star, ArrowRight, CheckCircle, Zap, Shield, Phone, ChevronRight, Sun, Battery, Cpu, Cable } from "lucide-react";
import { ImageWithFallback } from "@/components/figma/ImageWithFallback";

interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  originalPrice?: number;
  rating: number;
  reviews: number;
  badge?: string;
  category: string;
  watt?: string;
  image: string;
}

const PRODUCTS: Product[] = [
  {
    id: 1,
    name: "Q CELLS Q.PEAK DUO ML-G10+ 400W",
    description: "Monokristallines Hochleistungsmodul mit Anti-LID Technologie",
    price: 189.00,
    originalPrice: 219.00,
    rating: 4.9,
    reviews: 142,
    badge: "Bestseller",
    category: "pv",
    watt: "400 Wp",
    image: "https://images.unsplash.com/photo-1663321508309-4ceb96a3c791?w=400&h=300&fit=crop&auto=format",
  },
  {
    id: 2,
    name: "Huawei SUN2000-5KTL-M1 Wechselrichter",
    description: "Smart String Wechselrichter 5 kW mit integriertem WLAN",
    price: 849.00,
    rating: 4.8,
    reviews: 98,
    badge: "Empfohlen",
    category: "pv",
    watt: "5 kW",
    image: "https://images.unsplash.com/photo-1544724569-5f546fd6f2b5?w=400&h=300&fit=crop&auto=format",
  },
  {
    id: 3,
    name: "AlphaESS SMILE5 Batteriespeicher",
    description: "Dreiphasiger Hybridwechselrichter 5 kW mit 10,1 kWh Speicher",
    price: 4299.00,
    originalPrice: 4799.00,
    rating: 4.7,
    reviews: 63,
    badge: "Angebot",
    category: "battery",
    watt: "10,1 kWh",
    image: "https://images.unsplash.com/photo-1635335874521-7987db781153?w=400&h=300&fit=crop&auto=format",
  },
  {
    id: 4,
    name: "Victron Energy SmartSolar MPPT 100/50",
    description: "Bluetooth Solar-Laderegler mit Remote-Konfiguration",
    price: 299.00,
    rating: 4.9,
    reviews: 211,
    badge: "Top-Qualität",
    category: "parts",
    watt: "100V / 50A",
    image: "https://images.unsplash.com/photo-1544724569-5f546fd6f2b5?w=400&h=300&fit=crop&auto=format",
  },
  {
    id: 5,
    name: "Fronius Symo 8.2-3-M Wechselrichter",
    description: "Dreiphasiger Netzwechselrichter 8,2 kW mit DataManager",
    price: 1249.00,
    rating: 4.8,
    reviews: 77,
    category: "pv",
    watt: "8,2 kW",
    image: "https://images.unsplash.com/photo-1663321508309-4ceb96a3c791?w=400&h=300&fit=crop&auto=format",
  },
  {
    id: 6,
    name: "Photovoltaik-Kabel 6mm² rot/schwarz",
    description: "UV-beständiges Solar DC-Kabel, doppelt isoliert, Meterware",
    price: 1.89,
    rating: 4.6,
    reviews: 445,
    category: "parts",
    watt: "per Meter",
    image: "https://images.unsplash.com/photo-1635335874521-7987db781153?w=400&h=300&fit=crop&auto=format",
  },
];

const CATEGORIES = [
  {
    key: "pv",
    label: "PV-Anlagen",
    sublabel: "Solarmodule & Wechselrichter",
    icon: Sun,
    count: 184,
    color: "from-amber-400 to-orange-500",
    image: "https://images.unsplash.com/photo-1663321508309-4ceb96a3c791?w=600&h=400&fit=crop&auto=format",
  },
  {
    key: "battery",
    label: "Batteriespeicher",
    sublabel: "Stromspeicher & Hybridsysteme",
    icon: Battery,
    count: 56,
    color: "from-blue-500 to-cyan-500",
    image: "https://images.unsplash.com/photo-1635335874521-7987db781153?w=600&h=400&fit=crop&auto=format",
  },
  {
    key: "parts",
    label: "Elektroteile",
    sublabel: "Kabel, Stecker & Komponenten",
    icon: Cpu,
    count: 392,
    color: "from-slate-600 to-slate-800",
    image: "https://images.unsplash.com/photo-1544724569-5f546fd6f2b5?w=600&h=400&fit=crop&auto=format",
  },
  {
    key: "cables",
    label: "Leitungen",
    sublabel: "Energie- & Steuerleitungen",
    icon: Cable,
    count: 128,
    color: "from-emerald-500 to-teal-600",
    image: "https://images.unsplash.com/photo-1635335874521-7987db781153?w=600&h=400&fit=crop&auto=format",
  },
];

const BENEFITS = [
  { icon: CheckCircle, title: "Fachbetrieb seit 2017", text: "Zertifizierter Elektroinstallateur mit über 9 Jahren Erfahrung" },
  { icon: Zap, title: "2.150+ Projekte", text: "Erfolgreich realisierte Anlagen in der Region Sachsen-Anhalt" },
  { icon: Shield, title: "10 Jahre Garantie", text: "Auf alle verbauten Solarmodule und Systemkomponenten" },
  { icon: Phone, title: "Persönliche Beratung", text: "Kostenlos und unverbindlich – vor Ort oder telefonisch" },
];

interface ShopPageProps {
  onAddToCart: (product: Product) => void;
  activeCategory: string;
  onCategoryChange: (cat: string) => void;
  onProductClick: (product: Product) => void;
}

export function ShopPage({ onAddToCart, activeCategory, onCategoryChange, onProductClick }: ShopPageProps) {
  const [addedId, setAddedId] = useState<number | null>(null);

  const handleAdd = (product: Product) => {
    onAddToCart(product);
    setAddedId(product.id);
    setTimeout(() => setAddedId(null), 1500);
  };

  const filtered = activeCategory === "all"
    ? PRODUCTS
    : PRODUCTS.filter((p) => p.category === activeCategory);

  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
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
              <span className="text-accent text-xs font-semibold tracking-wider uppercase">Ihr Solar-Fachbetrieb</span>
            </div>
            <h1 className="text-white mb-5 leading-tight" style={{ fontFamily: "var(--font-display)", fontSize: "clamp(2rem, 5vw, 3.25rem)", fontWeight: 800 }}>
              Solarenergie & Elektrotechnik<br />
              <span className="text-accent">direkt vom Fachbetrieb</span>
            </h1>
            <p className="text-white/70 mb-8 max-w-xl leading-relaxed" style={{ fontSize: "1.05rem" }}>
              Hochwertige PV-Anlagen, Batteriespeicher und Elektroteile — kompetent beraten, schnell geliefert, professionell installiert.
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

          {/* Stats card */}
          <div className="hidden md:grid grid-cols-2 gap-px bg-white/10 rounded-xl overflow-hidden shrink-0 w-64">
            {[
              { value: "2.150+", label: "Projekte" },
              { value: "9 Jahre", label: "Erfahrung" },
              { value: "10 J.", label: "Garantie" },
              { value: "100%", label: "Kundenzufriedenheit" },
            ].map((s) => (
              <div key={s.label} className="bg-white/5 px-5 py-4 text-center backdrop-blur-sm">
                <div className="text-accent font-bold mb-0.5" style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem" }}>{s.value}</div>
                <div className="text-white/60 text-xs">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Category tiles */}
      <section className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex items-end justify-between mb-7">
          <div>
            <h2 className="text-foreground mb-1" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>Produktkategorien</h2>
            <p className="text-muted-foreground text-sm">Finden Sie die richtigen Komponenten für Ihr Projekt</p>
          </div>
          <button
            onClick={() => onCategoryChange("all")}
            className="text-sm text-accent font-semibold flex items-center gap-1 hover:gap-2 transition-all"
          >
            Alle anzeigen <ChevronRight size={15} />
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeCategory === cat.key;
            return (
              <button
                key={cat.key}
                onClick={() => onCategoryChange(cat.key)}
                className={`relative overflow-hidden rounded-xl text-left group border-2 transition-all duration-200 ${
                  isActive ? "border-accent shadow-lg" : "border-transparent hover:border-accent/30"
                }`}
                style={{ minHeight: 160 }}
              >
                <ImageWithFallback
                  src={cat.image}
                  alt={cat.label}
                  className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className={`absolute inset-0 bg-gradient-to-t ${cat.color} opacity-80`} />
                {isActive && <div className="absolute inset-0 ring-2 ring-accent rounded-xl" />}
                <div className="relative p-4 flex flex-col h-full justify-between text-white" style={{ minHeight: 160 }}>
                  <Icon size={22} className="opacity-90" />
                  <div>
                    <div className="font-bold leading-tight mb-0.5" style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem" }}>{cat.label}</div>
                    <div className="text-white/70 text-xs mb-1">{cat.sublabel}</div>
                    <div className="text-white/60 text-xs">{cat.count} Artikel</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Products grid */}
      <section className="max-w-7xl mx-auto px-4 pb-12">
        <div className="flex items-end justify-between mb-6">
          <h2 className="text-foreground" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {activeCategory === "all" ? "Alle Produkte" : CATEGORIES.find(c => c.key === activeCategory)?.label ?? "Produkte"}
          </h2>
          <span className="text-muted-foreground text-sm">{filtered.length} Artikel</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((product) => (
            <div key={product.id} className="bg-card border border-border rounded-xl overflow-hidden flex flex-col hover:shadow-md transition-shadow group cursor-pointer" onClick={() => onProductClick(product)}>
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
                <h3 className="text-foreground mb-1 leading-snug" style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: "0.9rem" }}>
                  {product.name}
                </h3>
                <p className="text-muted-foreground text-xs mb-3 leading-relaxed flex-1">{product.description}</p>
                <div className="flex items-center gap-1.5 mb-3">
                  <div className="flex">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} size={11} className={i < Math.floor(product.rating) ? "text-accent fill-accent" : "text-muted-foreground"} />
                    ))}
                  </div>
                  <span className="text-muted-foreground text-xs">({product.reviews})</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-foreground font-bold" style={{ fontFamily: "var(--font-display)", fontSize: "1.15rem" }}>
                      {product.price.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                    </span>
                    {product.originalPrice && (
                      <span className="text-muted-foreground text-xs line-through ml-2">
                        {product.originalPrice.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleAdd(product); }}
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
      </section>

      {/* Benefits section */}
      <section className="bg-primary py-14">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-white text-center mb-10" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.6rem" }}>
            Warum <span className="text-accent">König 39</span>?
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {BENEFITS.map((b) => {
              const Icon = b.icon;
              return (
                <div key={b.title} className="text-center p-6 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                  <div className="w-12 h-12 rounded-lg bg-accent/20 flex items-center justify-center mx-auto mb-4">
                    <Icon size={22} className="text-accent" />
                  </div>
                  <h3 className="text-white mb-2" style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: "0.95rem" }}>{b.title}</h3>
                  <p className="text-white/60 text-xs leading-relaxed">{b.text}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="bg-accent py-10">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h2 className="text-primary mb-1" style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: "1.4rem" }}>
              Kostenlose Beratung vereinbaren
            </h2>
            <p className="text-primary/70 text-sm">Wir planen Ihre individuelle PV-Anlage — unverbindlich und vor Ort.</p>
          </div>
          <div className="flex gap-3 shrink-0">
            <a href="tel:+493912345678" className="px-6 py-3 bg-primary text-white font-bold rounded flex items-center gap-2 hover:bg-primary/90 transition-colors text-sm">
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
