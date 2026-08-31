"use client";
import {FormEvent, useEffect, useState} from "react";
import {
    ArrowLeft,
    CheckCircle,
    ChevronDown,
    ChevronUp,
    Euro,
    Info,
    Leaf,
    Loader2,
    MessageSquareText,
    Pencil,
    Shield,
    ShoppingCart,
    Star,
    Sun,
    Trash2,
    TrendingUp,
    Zap
} from "lucide-react";
import {ImageWithFallback} from "@/src/components/figma/ImageWithFallback";
import {Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";

import {useApp} from "@/src/providers/AppProvider";
import {ApiError} from "@/src/lib/api";
import {deleteReview, fetchReviewsForItem, submitReview, type Review} from "@/src/lib/reviews";
import type {CatalogProduct} from "@/src/types/catalog";

interface ProductDetailProps {
    product: CatalogProduct;
    onBack: () => void;
    onAddToCart: (product: CatalogProduct, qty: number) => void;
}

const SUNHOURS_BY_REGION: Record<string, number> = {
    "Magdeburg": 1030,
    "Berlin": 990,
    "Hamburg": 940,
    "München": 1110,
    "Frankfurt": 1000,
    "Köln": 970,
    "Stuttgart": 1060,
    "Nürnberg": 1020,
};

const ORIENTATION_FACTOR: Record<string, number> = {
    "Süd": 1.0,
    "Süd-West": 0.95,
    "Süd-Ost": 0.95,
    "Ost-West": 0.85,
    "Ost": 0.75,
    "West": 0.75,
};

const TILT_FACTOR: Record<number, number> = {
    15: 0.90, 20: 0.94, 25: 0.97, 30: 1.0, 35: 0.99, 40: 0.97, 45: 0.94, 50: 0.90, 60: 0.82
};

const MONTHLY_DISTRIBUTION = [0.04, 0.06, 0.08, 0.10, 0.12, 0.13, 0.13, 0.11, 0.09, 0.07, 0.04, 0.03];
const MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];

export function ProductDetail({product, onBack, onAddToCart}: ProductDetailProps) {
    const [qty, setQty] = useState(1);
    const [addedPulse, setAddedPulse] = useState(false);

    // Bewertungen (siehe ADR 0019)
    const {user, isLoggedIn} = useApp();
    const [reviews, setReviews] = useState<Review[]>([]);
    const [reviewsLoading, setReviewsLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        setReviewsLoading(true);
        fetchReviewsForItem(product.id)
            .then((data) => {
                if (!cancelled) setReviews(data);
            })
            .catch(() => {
                if (!cancelled) setReviews([]);
            })
            .finally(() => {
                if (!cancelled) setReviewsLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [product.id]);

    const ownReview = user ? reviews.find((r) => r.customer_id === user.id) ?? null : null;

    const handleReviewSubmitted = (review: Review) => {
        setReviews((current) => {
            const withoutOwn = current.filter((r) => r.id !== review.id);
            return [review, ...withoutOwn];
        });
    };

    const handleReviewDeleted = (reviewId: number) => {
        setReviews((current) => current.filter((r) => r.id !== reviewId));
    };

    // Configurator state
    const [moduleCount, setModuleCount] = useState(12);
    const [orientation, setOrientation] = useState("Süd");
    const [tilt, setTilt] = useState(30);
    const [region, setRegion] = useState("Magdeburg");
    const [electricityPrice, setElectricityPrice] = useState(0.32);
    const [showSpecs, setShowSpecs] = useState(false);

    // Power calculation
    const wattPeak = product.category === "pv" ? (parseFloat(product.watt ?? "400") || 400) : 0;
    const systemKwp = (moduleCount * wattPeak) / 1000;
    const sunHours = SUNHOURS_BY_REGION[region] ?? 1000;
    const orientFactor = ORIENTATION_FACTOR[orientation] ?? 1.0;
    const closestTilt = [15, 20, 25, 30, 35, 40, 45, 50, 60].reduce((a, b) =>
        Math.abs(b - tilt) < Math.abs(a - tilt) ? b : a
    );
    const tiltFactor = TILT_FACTOR[closestTilt] ?? 1.0;
    const performanceRatio = 0.82;

    const annualKwh = Math.round(systemKwp * sunHours * orientFactor * tiltFactor * performanceRatio);
    const annualSavings = Math.round(annualKwh * electricityPrice);
    const co2Saved = Math.round(annualKwh * 0.380);
    const investmentCost = moduleCount * product.price * 1.19;
    const amortizationYears = (annualSavings > 0 ? investmentCost / annualSavings : 0).toFixed(1);

    const monthlyChartData = MONTHS.map((m, i) => ({
        month: m,
        kwh: Math.round(annualKwh * MONTHLY_DISTRIBUTION[i]),
        eur: Math.round(annualKwh * MONTHLY_DISTRIBUTION[i] * electricityPrice),
    }));

    const specs = product.specs ?? [];
    const isPVProduct = product.category === "pv";

    const handleAddToCart = () => {
        onAddToCart(product, qty);
        setAddedPulse(true);
        setTimeout(() => setAddedPulse(false), 1500);
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Breadcrumb */}
            <div className="border-b border-border bg-card">
                <div className="max-w-7xl mx-auto px-4 py-3">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-muted-foreground hover:text-accent transition-colors text-sm"
                    >
                        <ArrowLeft size={15}/>
                        Zurück zum Shop
                    </button>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Top section: image + purchase panel */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-10">
                    {/* Image */}
                    <div>
                        <div className="relative rounded-xl overflow-hidden bg-muted" style={{aspectRatio: "4/3"}}>
                            <ImageWithFallback
                                src={product.image}
                                alt={product.name}
                                className="w-full h-full object-cover"
                            />
                            {product.badge && (
                                <span
                                    className="absolute top-4 left-4 px-3 py-1 bg-accent text-primary text-xs font-bold rounded">
                  {product.badge}
                </span>
                            )}
                            {product.watt && (
                                <span
                                    className="absolute bottom-4 right-4 px-3 py-1.5 bg-primary/80 backdrop-blur-sm text-white text-sm font-bold rounded-lg"
                                    style={{fontFamily: "var(--font-display)"}}>
                  {product.watt}
                </span>
                            )}
                        </div>
                        {/* Thumbnail row (decorative) */}
                        <div className="grid grid-cols-4 gap-2 mt-2">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i}
                                     className={`rounded-lg overflow-hidden border-2 transition-colors cursor-pointer ${i === 1 ? "border-accent" : "border-border hover:border-accent/40"}`}
                                     style={{aspectRatio: "4/3"}}>
                                    <ImageWithFallback src={product.image} alt=""
                                                       className="w-full h-full object-cover opacity-80"/>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Purchase panel */}
                    <div className="flex flex-col">
                        <div>
                            <p className="text-accent text-xs font-semibold uppercase tracking-wider mb-2">
                                {product.category === "pv" ? "Solarmodule & Wechselrichter" :
                                    product.category === "battery" ? "Batteriespeicher" :
                                        product.category === "cables" ? "Leitungen" : "Elektroteile"}
                            </p>
                            <h1 className="text-foreground mb-3 leading-snug" style={{
                                fontFamily: "var(--font-display)",
                                fontWeight: 800,
                                fontSize: "clamp(1.3rem, 3vw, 1.8rem)"
                            }}>
                                {product.name}
                            </h1>

                            {/* Rating */}
                            <div className="flex items-center gap-2 mb-4">
                                <div className="flex">
                                    {Array.from({length: 5}).map((_, i) => (
                                        <Star key={i} size={14}
                                              className={i < Math.floor(product.rating) ? "text-accent fill-accent" : "text-muted-foreground"}/>
                                    ))}
                                </div>
                                <span className="text-foreground text-sm font-semibold">{product.rating}</span>
                                <span className="text-muted-foreground text-sm">({product.reviews} Bewertungen)</span>
                            </div>

                            <p className="text-muted-foreground text-sm leading-relaxed mb-5">{product.description}</p>

                            {/* Price */}
                            <div className="flex items-end gap-3 mb-5">
                <span className="text-foreground"
                      style={{fontFamily: "var(--font-display)", fontWeight: 800, fontSize: "2rem"}}>
                  {product.price.toLocaleString("de-DE", {style: "currency", currency: "EUR"})}
                </span>
                                {product.originalPrice && (
                                    <div className="mb-1">
                    <span className="text-muted-foreground text-sm line-through block">
                      {product.originalPrice.toLocaleString("de-DE", {style: "currency", currency: "EUR"})}
                    </span>
                                        <span className="text-green-600 text-xs font-semibold">
                      {Math.round((1 - product.price / product.originalPrice) * 100)} % Ersparnis
                    </span>
                                    </div>
                                )}
                            </div>

                            <p className="text-muted-foreground text-xs mb-5">Alle Preise inkl. MwSt. | Versandkosten ab
                                4,90 €</p>

                            {/* Quantity + Add to cart */}
                            <div className="flex items-center gap-3 mb-5">
                                <div className="flex items-center border border-border rounded-lg overflow-hidden">
                                    <button onClick={() => setQty(Math.max(1, qty - 1))}
                                            className="px-3 py-2.5 text-foreground hover:bg-muted transition-colors text-sm font-bold">−
                                    </button>
                                    <span
                                        className="px-4 py-2.5 text-foreground font-semibold text-sm min-w-[2.5rem] text-center border-x border-border"
                                        style={{fontFamily: "var(--font-display)"}}>{qty}</span>
                                    <button onClick={() => setQty(qty + 1)}
                                            className="px-3 py-2.5 text-foreground hover:bg-muted transition-colors text-sm font-bold">+
                                    </button>
                                </div>
                                <button
                                    onClick={handleAddToCart}
                                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg font-bold text-sm transition-all duration-200 ${
                                        addedPulse ? "bg-green-500 text-white scale-95" : "bg-primary text-primary-foreground hover:bg-primary/90"
                                    }`}
                                    style={{fontFamily: "var(--font-display)"}}
                                >
                                    <ShoppingCart size={16}/>
                                    {addedPulse ? "Hinzugefügt!" : `In den Warenkorb (${(product.price * qty).toLocaleString("de-DE", {
                                        style: "currency",
                                        currency: "EUR"
                                    })})`}
                                </button>
                            </div>

                            {/* Trust badges */}
                            <div className="grid grid-cols-3 gap-2">
                                {[
                                    {icon: Shield, label: "10 J. Garantie"},
                                    {icon: CheckCircle, label: "Fachbetrieb"},
                                    {icon: Zap, label: "Schnelllieferung"},
                                ].map((b) => {
                                    const Icon = b.icon;
                                    return (
                                        <div key={b.label}
                                             className="flex flex-col items-center gap-1 p-2.5 bg-muted/50 rounded-lg border border-border text-center">
                                            <Icon size={16} className="text-accent"/>
                                            <span className="text-muted-foreground text-xs">{b.label}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>

                {/* PV Configurator — only for PV products */}
                {isPVProduct && (
                    <div className="bg-primary rounded-2xl p-6 md:p-8 mb-8 text-white">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                                <Sun size={20} className="text-accent"/>
                            </div>
                            <div>
                                <h2 className="text-white"
                                    style={{fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.2rem"}}>
                                    PV-Ertragsrechner
                                </h2>
                                <p className="text-white/50 text-xs">Berechnen Sie Ihren individuellen Jahresertrag</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Left: Controls */}
                            <div className="space-y-5">
                                {/* Module count */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-white/80 text-sm font-semibold">Anzahl Module</label>
                                        <span className="text-accent font-bold"
                                              style={{fontFamily: "var(--font-display)", fontSize: "1.1rem"}}>
                      {moduleCount} × {wattPeak} Wp = {systemKwp.toFixed(1)} kWp
                    </span>
                                    </div>
                                    <input
                                        type="range"
                                        min={4}
                                        max={40}
                                        step={1}
                                        value={moduleCount}
                                        onChange={(e) => setModuleCount(Number(e.target.value))}
                                        className="w-full accent-[#F5A623] cursor-pointer"
                                    />
                                    <div className="flex justify-between text-white/30 text-xs mt-1">
                                        <span>4 Module</span><span>40 Module</span>
                                    </div>
                                </div>

                                {/* Orientation */}
                                <div>
                                    <label
                                        className="text-white/80 text-sm font-semibold block mb-2">Ausrichtung</label>
                                    <div className="grid grid-cols-3 gap-1.5">
                                        {Object.keys(ORIENTATION_FACTOR).map((o) => (
                                            <button
                                                key={o}
                                                onClick={() => setOrientation(o)}
                                                className={`px-2 py-2 rounded text-xs font-semibold transition-colors ${
                                                    orientation === o
                                                        ? "bg-accent text-primary"
                                                        : "bg-white/10 text-white/70 hover:bg-white/20"
                                                }`}
                                            >
                                                {o}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Tilt */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-white/80 text-sm font-semibold">Dachneigung</label>
                                        <span className="text-accent font-bold">{tilt}°</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={15}
                                        max={60}
                                        step={5}
                                        value={tilt}
                                        onChange={(e) => setTilt(Number(e.target.value))}
                                        className="w-full accent-[#F5A623] cursor-pointer"
                                    />
                                    <div className="flex justify-between text-white/30 text-xs mt-1">
                                        <span>15° (flach)</span><span>60° (steil)</span>
                                    </div>
                                </div>

                                {/* Region */}
                                <div>
                                    <label className="text-white/80 text-sm font-semibold block mb-2">Standort</label>
                                    <select
                                        value={region}
                                        onChange={(e) => setRegion(e.target.value)}
                                        className="w-full px-3 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                                    >
                                        {Object.keys(SUNHOURS_BY_REGION).map((r) => (
                                            <option key={r} value={r}
                                                    className="text-foreground bg-card">{r} ({SUNHOURS_BY_REGION[r]} Sonnenstunden/Jahr)</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Electricity price */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-white/80 text-sm font-semibold">Strompreis</label>
                                        <span
                                            className="text-accent font-bold">{electricityPrice.toFixed(2)} €/kWh</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0.20}
                                        max={0.50}
                                        step={0.01}
                                        value={electricityPrice}
                                        onChange={(e) => setElectricityPrice(Number(e.target.value))}
                                        className="w-full accent-[#F5A623] cursor-pointer"
                                    />
                                    <div className="flex justify-between text-white/30 text-xs mt-1">
                                        <span>0,20 €</span><span>0,50 €</span>
                                    </div>
                                </div>
                            </div>

                            {/* Right: Results */}
                            <div className="space-y-4">
                                {/* KPI Grid */}
                                <div className="grid grid-cols-2 gap-3">
                                    {[
                                        {
                                            icon: Zap,
                                            label: "Jahresertrag",
                                            value: `${annualKwh.toLocaleString("de-DE")} kWh`,
                                            color: "text-amber-300"
                                        },
                                        {
                                            icon: Euro,
                                            label: "Jahreseinsparung",
                                            value: `${annualSavings.toLocaleString("de-DE")} €`,
                                            color: "text-green-400"
                                        },
                                        {
                                            icon: Leaf,
                                            label: "CO₂ eingespart",
                                            value: `${co2Saved.toLocaleString("de-DE")} kg`,
                                            color: "text-emerald-400"
                                        },
                                        {
                                            icon: TrendingUp,
                                            label: "Amortisation",
                                            value: `${amortizationYears} Jahre`,
                                            color: "text-blue-300"
                                        },
                                    ].map((kpi) => {
                                        const Icon = kpi.icon;
                                        return (
                                            <div key={kpi.label} className="bg-white/10 rounded-xl p-4">
                                                <Icon size={18} className={`${kpi.color} mb-2`}/>
                                                <div className="text-white font-bold mb-0.5"
                                                     style={{fontFamily: "var(--font-display)", fontSize: "1.15rem"}}>
                                                    {kpi.value}
                                                </div>
                                                <div className="text-white/50 text-xs">{kpi.label}</div>
                                            </div>
                                        );
                                    })}
                                </div>

                                {/* Monthly chart */}
                                <div className="bg-white/10 rounded-xl p-4">
                                    <p className="text-white/60 text-xs mb-3">Monatliche Ertragsprognose</p>
                                    <ResponsiveContainer width="100%" height={130}>
                                        <AreaChart data={monthlyChartData}>
                                            <defs>
                                                <linearGradient id="cfgGrad" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#F5A623" stopOpacity={0.4}/>
                                                    <stop offset="95%" stopColor="#F5A623" stopOpacity={0}/>
                                                </linearGradient>
                                            </defs>
                                            <XAxis dataKey="month" tick={{fontSize: 10, fill: "rgba(255,255,255,0.5)"}}
                                                   axisLine={false} tickLine={false}/>
                                            <YAxis hide/>
                                            <Tooltip
                                                formatter={(v: number) => [`${v} kWh`, "Ertrag"]}
                                                contentStyle={{
                                                    background: "#0B2545",
                                                    border: "1px solid rgba(255,255,255,0.1)",
                                                    borderRadius: 6,
                                                    fontSize: 11,
                                                    color: "#fff"
                                                }}
                                            />
                                            <Area type="monotone" dataKey="kwh" stroke="#F5A623" strokeWidth={2}
                                                  fill="url(#cfgGrad)"/>
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* Investment summary */}
                                <div className="bg-accent/20 border border-accent/30 rounded-xl p-4">
                                    <div className="flex items-start gap-2">
                                        <Info size={15} className="text-accent mt-0.5 shrink-0"/>
                                        <div>
                                            <p className="text-white text-xs font-semibold mb-1">Investitionsübersicht</p>
                                            <p className="text-white/70 text-xs leading-relaxed">
                                                {moduleCount} × {product.name.split(" ").slice(0, 3).join(" ")} = <strong
                                                className="text-white">{investmentCost.toLocaleString("de-DE", {
                                                style: "currency",
                                                currency: "EUR"
                                            })}</strong> (inkl. MwSt.)<br/>
                                                Einsparung Jahr 1: <strong
                                                className="text-accent">{annualSavings.toLocaleString("de-DE")} €</strong> ·
                                                Amortisation: <strong
                                                className="text-white">{amortizationYears} Jahre</strong>
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Technical Specs */}
                <div className="bg-card border border-border rounded-xl mb-8">
                    <button
                        onClick={() => setShowSpecs(!showSpecs)}
                        className="w-full flex items-center justify-between px-6 py-4 text-left"
                    >
                        <h2 className="text-foreground"
                            style={{fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem"}}>
                            Technische Daten
                        </h2>
                        {showSpecs ? <ChevronUp size={18} className="text-muted-foreground"/> :
                            <ChevronDown size={18} className="text-muted-foreground"/>}
                    </button>
                    {showSpecs && (
                        <div className="px-6 pb-6 border-t border-border">
                            {specs.length === 0 ? (
                                <p className="pt-4 text-muted-foreground text-xs">Keine technischen Daten
                                    hinterlegt.</p>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12">
                                    {specs.map((s, i) => (
                                        <div key={`${s.label}-${i}`}
                                             className={`flex items-start justify-between py-2.5 ${i < specs.length - 1 ? "border-b border-border" : ""}`}>
                                            <span className="text-muted-foreground text-xs">{s.label}</span>
                                            <span
                                                className="text-foreground text-xs font-semibold text-right ml-4">{s.value}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Bewertungen (siehe ADR 0019) */}
                <div className="bg-card border border-border rounded-xl p-6 mb-8">
                    <div className="flex items-center gap-2 mb-5">
                        <MessageSquareText size={18} className="text-accent"/>
                        <h2 className="text-foreground"
                            style={{fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem"}}>
                            Bewertungen ({product.reviews})
                        </h2>
                    </div>

                    {isLoggedIn ? (
                        <ReviewForm
                            itemId={product.id}
                            existingReview={ownReview}
                            onSaved={handleReviewSubmitted}
                            onDeleted={handleReviewDeleted}
                        />
                    ) : (
                        <p className="text-muted-foreground text-xs mb-5">
                            Bitte melden Sie sich an, um eine Bewertung abzugeben.
                        </p>
                    )}

                    <ReviewList reviews={reviews} loading={reviewsLoading} ownUserId={user?.id ?? null}/>
                </div>
            </div>
        </div>
    );
}

function StarRatingDisplay({rating, size = 14}: { rating: number; size?: number }) {
    return (
        <div className="flex">
            {Array.from({length: 5}).map((_, i) => (
                <Star key={i} size={size}
                      className={i < Math.round(rating) ? "text-accent fill-accent" : "text-muted-foreground"}/>
            ))}
        </div>
    );
}

function ReviewList({reviews, loading, ownUserId}: {
    reviews: Review[];
    loading: boolean;
    ownUserId: number | null;
}) {
    if (loading) {
        return (
            <div className="flex items-center gap-2 text-muted-foreground text-xs py-4">
                <Loader2 size={14} className="animate-spin"/>
                Bewertungen werden geladen…
            </div>
        );
    }

    const others = reviews.filter((r) => r.customer_id !== ownUserId);

    if (others.length === 0) {
        return (
            <p className="text-muted-foreground text-xs py-2">
                Für diesen Artikel liegen noch keine Bewertungen vor.
            </p>
        );
    }

    return (
        <div className="space-y-4 mt-2">
            {others.map((review) => (
                <div key={review.id} className="border-t border-border pt-4 first:border-t-0 first:pt-0">
                    <div className="flex items-center justify-between mb-1.5">
                        <span className="text-foreground text-sm font-semibold">{review.customer}</span>
                        <span className="text-muted-foreground text-xs">
              {new Date(review.created_at).toLocaleDateString("de-DE")}
            </span>
                    </div>
                    <StarRatingDisplay rating={review.rating}/>
                    {review.comment && (
                        <p className="text-muted-foreground text-sm leading-relaxed mt-2">{review.comment}</p>
                    )}
                </div>
            ))}
        </div>
    );
}

function ReviewForm({itemId, existingReview, onSaved, onDeleted}: {
    itemId: number;
    existingReview: Review | null;
    onSaved: (review: Review) => void;
    onDeleted: (reviewId: number) => void;
}) {
    const [editing, setEditing] = useState(false);
    const [rating, setRating] = useState(existingReview?.rating ?? 0);
    const [hoverRating, setHoverRating] = useState(0);
    const [comment, setComment] = useState(existingReview?.comment ?? "");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const startEditing = () => {
        setRating(existingReview?.rating ?? 0);
        setComment(existingReview?.comment ?? "");
        setError(null);
        setEditing(true);
    };

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();
        setError(null);

        if (rating < 1) {
            setError("Bitte wählen Sie eine Sternebewertung aus.");
            return;
        }

        setIsSubmitting(true);
        try {
            const review = await submitReview(itemId, rating, comment.trim());
            onSaved(review);
            setEditing(false);
        } catch (err) {
            if (err instanceof ApiError && err.status === 403) {
                setError("Sie können nur Artikel bewerten, die Sie bereits gekauft haben.");
            } else {
                const message =
                    err instanceof ApiError
                        ? [...err.generalErrors, ...Object.values(err.fieldErrors).flat()].join(" ") ||
                        err.message
                        : "Bewertung konnte nicht gespeichert werden. Bitte versuchen Sie es erneut.";
                setError(message);
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!existingReview) return;
        setIsDeleting(true);
        setError(null);
        try {
            await deleteReview(existingReview.id);
            onDeleted(existingReview.id);
            setEditing(false);
        } catch {
            setError("Bewertung konnte nicht gelöscht werden. Bitte versuchen Sie es erneut.");
        } finally {
            setIsDeleting(false);
        }
    };

    if (existingReview && !editing) {
        return (
            <div className="mb-5 p-4 bg-muted/20 border border-border rounded-lg">
                <div className="flex items-center justify-between mb-1.5">
                    <span className="text-foreground text-sm font-semibold">Ihre Bewertung</span>
                    <div className="flex items-center gap-1.5">
                        <button
                            type="button"
                            onClick={startEditing}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground"
                            title="Bewertung bearbeiten"
                        >
                            <Pencil size={14}/>
                        </button>
                        <button
                            type="button"
                            onClick={handleDelete}
                            disabled={isDeleting}
                            className="p-1.5 rounded hover:bg-muted text-destructive disabled:opacity-50"
                            title="Bewertung löschen"
                        >
                            {isDeleting ? <Loader2 size={14} className="animate-spin"/> : <Trash2 size={14}/>}
                        </button>
                    </div>
                </div>
                <StarRatingDisplay rating={existingReview.rating}/>
                {existingReview.comment && (
                    <p className="text-muted-foreground text-sm leading-relaxed mt-2">{existingReview.comment}</p>
                )}
                {error && <p className="text-destructive text-xs mt-2">{error}</p>}
            </div>
        );
    }

    return (
        <form onSubmit={handleSubmit}
              className="mb-5 p-4 bg-muted/20 border border-border rounded-lg space-y-3">
            <div>
                <label className="text-foreground text-sm font-semibold block mb-2">
                    {existingReview ? "Bewertung bearbeiten" : "Artikel bewerten"}
                </label>
                <div className="flex gap-1">
                    {Array.from({length: 5}).map((_, i) => {
                        const value = i + 1;
                        const filled = value <= (hoverRating || rating);
                        return (
                            <button
                                key={value}
                                type="button"
                                onClick={() => setRating(value)}
                                onMouseEnter={() => setHoverRating(value)}
                                onMouseLeave={() => setHoverRating(0)}
                                disabled={isSubmitting}
                                aria-label={`${value} von 5 Sternen`}
                                className="p-0.5"
                            >
                                <Star size={22} className={filled ? "text-accent fill-accent" : "text-muted-foreground"}/>
                            </button>
                        );
                    })}
                </div>
            </div>

            <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
                maxLength={1000}
                disabled={isSubmitting}
                placeholder="Ihre Erfahrung mit diesem Artikel (optional) …"
                className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60 resize-none"
            />

            {error && (
                <div className="p-2.5 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive">
                    {error}
                </div>
            )}

            <div className="flex items-center gap-2">
                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-bold text-sm rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
                    style={{fontFamily: "var(--font-display)"}}
                >
                    {isSubmitting && <Loader2 size={14} className="animate-spin"/>}
                    {existingReview ? "Speichern" : "Bewertung absenden"}
                </button>
                {existingReview && (
                    <button
                        type="button"
                        onClick={() => {
                            setEditing(false);
                            setError(null);
                        }}
                        disabled={isSubmitting}
                        className="px-4 py-2 text-muted-foreground text-sm font-semibold rounded-lg hover:bg-muted transition-colors"
                    >
                        Abbrechen
                    </button>
                )}
            </div>
        </form>
    );
}
