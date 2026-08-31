"use client";
import { useEffect, useState } from "react";
import type { User } from "@/src/types/user";
import { getUserDisplayName, getUserInitials } from "@/src/types/user";
import {
  LayoutDashboard, ShoppingBag, FileText, Zap, ChevronRight,
  Download, CheckCircle, Clock, Package, AlertCircle,
  Sun, TrendingUp, Euro, LogOut, Bell, X, RotateCcw, Loader2
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar
} from "recharts";
import { DemoDataBadge } from "@/src/components/DemoDataBadge";
import { useApp } from "@/src/providers/AppProvider";
import {
  downloadInvoicePdf,
  fetchMyInvoices,
  type Invoice,
} from "@/src/lib/invoices";
import {
  fetchMyOrders,
  isActiveOrder,
  reorder,
  ORDER_STATUS_LABELS,
  type ConfirmedOrder,
} from "@/src/lib/orders";
import {
  fetchMyReturnRequests,
  RETURN_REQUEST_STATUS_LABELS,
  type ReturnRequest,
} from "@/src/lib/returns";
import {
  fetchNotifications,
  markNotificationsSeen,
  type NotificationEvent,
} from "@/src/lib/notifications";
import { ReturnRequestModal } from "@/src/components/ReturnRequestModal";

const NOTIFICATION_ICONS: Record<NotificationEvent["kind"], typeof Bell> = {
  order_created: ShoppingBag,
  order_paid: Euro,
  order_shipped: Package,
  order_delivered: CheckCircle,
  invoice_issued: FileText,
  return_status_changed: RotateCcw,
};

function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return "";
  const diffMin = Math.round((Date.now() - date.getTime()) / 60000);
  if (diffMin < 1) return "gerade eben";
  if (diffMin < 60) return `vor ${diffMin} Min.`;
  const diffHours = Math.round(diffMin / 60);
  if (diffHours < 24) return `vor ${diffHours} Std.`;
  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 30) return `vor ${diffDays} Tag${diffDays === 1 ? "" : "en"}`;
  return date.toLocaleDateString("de-DE");
}

const pvMonthlyData = [
  { month: "Jan", kwh: 120, eur: 43 },
  { month: "Feb", kwh: 210, eur: 76 },
  { month: "Mär", kwh: 380, eur: 137 },
  { month: "Apr", kwh: 520, eur: 187 },
  { month: "Mai", kwh: 680, eur: 245 },
  { month: "Jun", kwh: 720, eur: 259 },
  { month: "Jul", kwh: 695, eur: 250 },
  { month: "Aug", kwh: 640, eur: 230 },
  { month: "Sep", kwh: 490, eur: 176 },
  { month: "Okt", kwh: 310, eur: 112 },
  { month: "Nov", kwh: 160, eur: 58 },
  { month: "Dez", kwh: 95, eur: 34 },
];

const dailyData = [
  { time: "06:00", kw: 0.2 },
  { time: "08:00", kw: 1.1 },
  { time: "10:00", kw: 2.8 },
  { time: "12:00", kw: 4.2 },
  { time: "14:00", kw: 3.9 },
  { time: "16:00", kw: 2.5 },
  { time: "18:00", kw: 0.8 },
  { time: "20:00", kw: 0.0 },
];

const paymentStatusConfig = {
  paid: { color: "text-green-600", bg: "bg-green-50 border-green-200", icon: CheckCircle },
  pending: { color: "text-amber-600", bg: "bg-amber-50 border-amber-200", icon: Clock },
  failed: { color: "text-red-600", bg: "bg-red-50 border-red-200", icon: AlertCircle },
  cancelled: { color: "text-gray-500", bg: "bg-gray-50 border-gray-200", icon: Package },
} as const;

function formatOrderDate(isoDate: string): string {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("de-DE");
}

interface TimelineStep {
  label: string;
  done: boolean;
  date: string;
}

function buildOrderTimeline(order: ConfirmedOrder): TimelineStep[] {
  const steps: TimelineStep[] = [
    { label: "Bestellung eingegangen", done: true, date: formatOrderDate(order.created_at) },
    {
      label: "Zahlung bestätigt",
      done: !!order.paid_at,
      date: order.paid_at ? formatOrderDate(order.paid_at) : "",
    },
  ];
  if (order.payment_status === "paid") {
    steps.push({
      label: "In Bearbeitung",
      done: order.fulfillment_status !== "pending",
      date: "",
    });
    steps.push({
      label: order.tracking_number
        ? `Versandt (${order.carrier ?? ""} ${order.tracking_number})`
        : "Versandt",
      done: !!order.shipped_at,
      date: order.shipped_at ? formatOrderDate(order.shipped_at) : "",
    });
    steps.push({
      label: "Zugestellt",
      done: !!order.delivered_at,
      date: order.delivered_at ? formatOrderDate(order.delivered_at) : "",
    });
  }
  return steps;
}

interface CustomerDashboardProps {
  user: User;
  onLogout: () => void;
}

export function CustomerDashboard({ onLogout, user }: CustomerDashboardProps) {
  const { addToCart } = useApp();
  const [activeTab, setActiveTab] = useState("overview");
  const [expandedOrder, setExpandedOrder] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [orders, setOrders] = useState<ConfirmedOrder[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState<string | null>(null);

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [invoicesLoading, setInvoicesLoading] = useState(true);
  const [invoicesError, setInvoicesError] = useState<string | null>(null);
  const [downloadingInvoiceId, setDownloadingInvoiceId] = useState<number | null>(null);

  const [returnRequests, setReturnRequests] = useState<ReturnRequest[]>([]);
  const [returnModalOrder, setReturnModalOrder] = useState<ConfirmedOrder | null>(null);

  const [reorderingOrderId, setReorderingOrderId] = useState<number | null>(null);
  const [reorderFeedback, setReorderFeedback] = useState<string | null>(null);

  const [notifications, setNotifications] = useState<NotificationEvent[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchMyOrders()
      .then((data) => {
        if (cancelled) return;
        setOrders(data);
        setExpandedOrder((current) => current ?? data[0]?.id ?? null);
      })
      .catch((err) => {
        if (!cancelled) {
          setOrdersError(
            err instanceof Error ? err.message : "Fehler beim Laden der Bestellungen"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setOrdersLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchMyInvoices()
      .then((data) => {
        if (cancelled) return;
        setInvoices(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setInvoicesError(
            err instanceof Error ? err.message : "Fehler beim Laden der Rechnungen"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setInvoicesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchMyReturnRequests()
      .then((data) => {
        if (!cancelled) setReturnRequests(data);
      })
      .catch(() => {
        // Rückgabe-Status ist eine ergänzende Anzeige - ein Fehler hier
        // soll das übrige Dashboard nicht blockieren.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Benachrichtigungsglocke (siehe ADR 0021): einmaliger Abruf beim
  // Öffnen des Dashboards, bewusst kein Live-Polling/WebSocket.
  useEffect(() => {
    let cancelled = false;
    fetchNotifications()
      .then((data) => {
        if (cancelled) return;
        setNotifications(data.results);
        setUnreadCount(data.unread_count);
      })
      .catch(() => {
        // Ergänzende Anzeige - ein Fehler hier soll das übrige Dashboard
        // nicht blockieren.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function latestReturnRequestForOrder(orderId: number): ReturnRequest | undefined {
    return returnRequests.find((r) => r.order === orderId);
  }

  async function handleToggleNotifications() {
    const opening = !notifOpen;
    setNotifOpen(opening);
    if (!opening || unreadCount === 0) return;

    setUnreadCount(0);
    setNotifications((current) => current.map((n) => ({ ...n, read: true })));
    try {
      await markNotificationsSeen();
    } catch {
      // Best effort - beim nächsten Laden des Dashboards wird der
      // Gelesen-Status ohnehin serverseitig neu berechnet.
    }
  }

  async function handleReorder(order: ConfirmedOrder) {
    setReorderingOrderId(order.id);
    setReorderFeedback(null);
    try {
      const result = await reorder(order, addToCart);
      if (result.unavailable.length > 0) {
        const addedText =
          result.addedCount > 0
            ? `${result.addedCount} Artikel wurden in den Warenkorb gelegt.`
            : "Es konnte kein Artikel in den Warenkorb gelegt werden.";
        setReorderFeedback(
          `${addedText} ${result.unavailable.length} Artikel nicht verfügbar: ${result.unavailable.join(", ")}.`
        );
      } else if (result.addedCount > 0) {
        setReorderFeedback(`${result.addedCount} Artikel wurden erneut in den Warenkorb gelegt.`);
      } else {
        setReorderFeedback("Diese Bestellung enthält keine Artikel, die erneut bestellt werden können.");
      }
    } catch (err) {
      setReorderFeedback(
        err instanceof Error ? err.message : "Erneutes Bestellen ist fehlgeschlagen."
      );
    } finally {
      setReorderingOrderId(null);
    }
  }

  async function handleDownloadInvoice(invoiceId: number) {
    setDownloadingInvoiceId(invoiceId);
    try {
      await downloadInvoicePdf(invoiceId);
    } catch (err) {
      setInvoicesError(
        err instanceof Error ? err.message : "Rechnung konnte nicht heruntergeladen werden."
      );
    } finally {
      setDownloadingInvoiceId(null);
    }
  }

  const tabs = [
    { key: "overview", label: "Übersicht", icon: LayoutDashboard },
    { key: "orders", label: "Bestellungen", icon: ShoppingBag },
    { key: "invoices", label: "Rechnungen", icon: FileText },
    { key: "performance", label: "PV-Leistung", icon: Zap },
  ];

  const totalSaved = pvMonthlyData.reduce((s, m) => s + m.eur, 0);
  const totalKwh = pvMonthlyData.reduce((s, m) => s + m.kwh, 0);
  const displayName = getUserDisplayName(user);
  const initials = getUserInitials(user);
  const accountLabel = user.is_staff ? "Mitarbeiterkonto" : "Kundenkonto";

  const activeOrders = orders.filter(isActiveOrder);
  const pendingOrders = orders.filter((o) => o.payment_status === "pending");
  const latestOrder = orders[0];

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:sticky top-0 left-0 h-screen w-64 bg-primary flex flex-col z-50 transition-transform duration-300 shrink-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ maxHeight: "100dvh" }}
      >
        {/* Sidebar header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-accent flex items-center justify-center">
              <Sun size={16} className="text-primary" />
            </div>
            <div>
              <div className="text-white font-bold leading-none" style={{ fontFamily: "var(--font-display)", fontSize: "1rem" }}>
                KÖNIG<span className="text-accent">39</span>
              </div>
              <div className="text-white/40 leading-none mt-0.5" style={{ fontSize: "0.55rem", letterSpacing: "0.1em" }}>KUNDENPORTAL</div>
            </div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-white/50 hover:text-white">
            <X size={18} />
          </button>
        </div>

        {/* User info */}
        <div className="px-4 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-accent/20 flex items-center justify-center text-accent text-xs font-bold">
              {initials}
            </div>
            <div className="min-w-0">
              <div className="text-white text-sm font-semibold truncate">
                {displayName}
              </div>
              <div className="text-white/40 text-xs truncate">{user.email}</div>
              <div className="text-white/30 text-[0.65rem] mt-0.5">
                {accountLabel} · {user.customer_number}
              </div>
            </div>
          </div>
        </div>
        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => { setActiveTab(tab.key); setSidebarOpen(false); }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 text-left ${
                  isActive
                    ? "bg-accent text-primary font-bold"
                    : "text-white/70 hover:text-white hover:bg-white/10"
                }`}
              >
                <Icon size={17} />
                {tab.label}
                {isActive && <ChevronRight size={14} className="ml-auto" />}
              </button>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="p-4 border-t border-white/10">
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-white/60 hover:text-white hover:bg-white/10 rounded-lg text-sm transition-colors"
          >
            <LogOut size={15} /> Abmelden
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Topbar */}
        <header className="bg-card border-b border-border px-4 md:px-6 py-3.5 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-1.5 rounded hover:bg-muted text-foreground"
            >
              <LayoutDashboard size={18} />
            </button>
            <div>
              <h1 className="text-foreground leading-none" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.05rem" }}>
                {tabs.find(t => t.key === activeTab)?.label}
              </h1>
              <p className="text-muted-foreground text-xs mt-0.5">
                Willkommen zurück, {user.first_name || displayName}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 relative">
            <button
              onClick={handleToggleNotifications}
              className="relative p-2 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            >
              <Bell size={17} />
              {unreadCount > 0 && (
                <span className="absolute top-0.5 right-0.5 min-w-[15px] h-[15px] px-0.5 rounded-full bg-accent text-primary text-[0.6rem] font-bold flex items-center justify-center leading-none">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </button>
            {notifOpen && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setNotifOpen(false)} />
                <div className="absolute right-0 top-full mt-2 w-80 max-w-[90vw] bg-card border border-border rounded-xl shadow-2xl z-40 overflow-hidden">
                  <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                    <span className="text-foreground font-semibold text-sm">Benachrichtigungen</span>
                    <button
                      onClick={() => setNotifOpen(false)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <div className="max-h-80 overflow-y-auto divide-y divide-border">
                    {notifications.length === 0 && (
                      <p className="text-muted-foreground text-xs px-4 py-6 text-center">
                        Keine Benachrichtigungen vorhanden.
                      </p>
                    )}
                    {notifications.map((notification, idx) => {
                      const Icon = NOTIFICATION_ICONS[notification.kind] ?? Bell;
                      return (
                        <div
                          key={`${notification.kind}-${notification.order_id}-${idx}`}
                          className={`flex items-start gap-3 px-4 py-3 ${
                            !notification.read ? "bg-accent/5" : ""
                          }`}
                        >
                          <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center shrink-0 mt-0.5">
                            <Icon size={13} className="text-accent" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-foreground text-xs leading-snug">
                              {notification.message}
                            </p>
                            <p className="text-muted-foreground text-[0.65rem] mt-0.5">
                              {formatRelativeTime(notification.occurred_at)}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 md:p-6 overflow-auto">
          {reorderFeedback && (
            <div className="mb-4 flex items-start justify-between gap-3 px-4 py-3 rounded-lg border border-accent/30 bg-accent/10 text-sm text-foreground">
              <span>{reorderFeedback}</span>
              <button
                onClick={() => setReorderFeedback(null)}
                className="text-muted-foreground hover:text-foreground shrink-0"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {/* OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <div className="bg-card border border-border rounded-xl p-5">
                <h2
                  className="text-foreground mb-4"
                  style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem" }}
                >
                  Mein Profil
                </h2>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1">Name</dt>
                    <dd className="text-foreground font-medium">{displayName}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1">E-Mail</dt>
                    <dd className="text-foreground font-medium">{user.email}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1">Kundennummer</dt>
                    <dd className="text-foreground font-medium">{user.customer_number}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1">Kontostatus</dt>
                    <dd className="text-foreground font-medium">
                      {user.is_active ? "Aktiv" : "Inaktiv"}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* KPI cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  {
                    label: "Aktive Bestellungen",
                    value: ordersLoading ? "…" : String(activeOrders.length),
                    sub: ordersLoading
                      ? "wird geladen …"
                      : pendingOrders.length > 0
                      ? `${pendingOrders.length} Zahlung ausstehend`
                      : "Alle bezahlt",
                    icon: ShoppingBag, color: "text-blue-600", bg: "bg-blue-50", demo: false,
                  },
                  { label: "Offene Rechnungen", value: "1", sub: "393,50 €", icon: FileText, color: "text-amber-600", bg: "bg-amber-50", demo: true },
                  { label: "Jahresertrag", value: `${totalKwh.toLocaleString("de-DE")} kWh`, sub: "seit Jan 2025", icon: Zap, color: "text-green-600", bg: "bg-green-50", demo: true },
                  { label: "Einsparungen", value: `${totalSaved.toLocaleString("de-DE")} €`, sub: "Stromkosten gespart", icon: Euro, color: "text-purple-600", bg: "bg-purple-50", demo: true },
                ].map((card) => {
                  const Icon = card.icon;
                  return (
                    <div key={card.label} className="bg-card border border-border rounded-xl p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className={`w-9 h-9 rounded-lg ${card.bg} flex items-center justify-center`}>
                          <Icon size={18} className={card.color} />
                        </div>
                        <TrendingUp size={13} className="text-muted-foreground mt-1" />
                      </div>
                      <div className="text-foreground mb-0.5" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.25rem" }}>{card.value}</div>
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <div className="text-muted-foreground text-xs">{card.label}</div>
                        {card.demo && <DemoDataBadge />}
                      </div>
                      <div className="text-muted-foreground text-xs opacity-70">{card.sub}</div>
                    </div>
                  );
                })}
              </div>

              {/* Latest order */}
              <div className="bg-card border border-border rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-foreground" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem" }}>Letzte Bestellung</h2>
                  <button onClick={() => setActiveTab("orders")} className="text-accent text-xs font-semibold flex items-center gap-1">
                    Alle anzeigen <ChevronRight size={13} />
                  </button>
                </div>
                {ordersLoading && <p className="text-muted-foreground text-sm">Bestellungen werden geladen …</p>}
                {ordersError && <p className="text-destructive text-sm">{ordersError}</p>}
                {!ordersLoading && !ordersError && !latestOrder && (
                  <p className="text-muted-foreground text-sm">Noch keine Bestellungen vorhanden.</p>
                )}
                {latestOrder && (
                  <OrderCard
                    order={latestOrder}
                    expanded={true}
                    onToggle={() => {}}
                    returnRequest={latestReturnRequestForOrder(latestOrder.id)}
                    onRequestReturn={setReturnModalOrder}
                    onReorder={handleReorder}
                    reordering={reorderingOrderId === latestOrder.id}
                  />
                )}
              </div>

              {/* Monthly chart preview */}
              <div className="bg-card border border-border rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <h2 className="text-foreground" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem" }}>PV-Ertrag 2025</h2>
                    <DemoDataBadge />
                  </div>
                  <button onClick={() => setActiveTab("performance")} className="text-accent text-xs font-semibold flex items-center gap-1">
                    Details <ChevronRight size={13} />
                  </button>
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <AreaChart data={pvMonthlyData}>
                    <defs>
                      <linearGradient id="pvGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F5A623" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#F5A623" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#5A738A" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#5A738A" }} axisLine={false} tickLine={false} unit=" kWh" />
                    <Tooltip
                      formatter={(v: number) => [`${v} kWh`, "Ertrag"]}
                      contentStyle={{ border: "1px solid rgba(0,0,0,0.1)", borderRadius: 6, fontSize: 12 }}
                    />
                    <Area type="monotone" dataKey="kwh" stroke="#F5A623" strokeWidth={2} fill="url(#pvGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ORDERS */}
          {activeTab === "orders" && (
            <div className="space-y-4">
              {ordersLoading && (
                <p className="text-muted-foreground text-sm">Bestellungen werden geladen …</p>
              )}
              {ordersError && (
                <p className="text-destructive text-sm">{ordersError}</p>
              )}
              {!ordersLoading && !ordersError && orders.length === 0 && (
                <p className="text-muted-foreground text-sm">Noch keine Bestellungen vorhanden.</p>
              )}
              {orders.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  expanded={expandedOrder === order.id}
                  onToggle={() => setExpandedOrder(expandedOrder === order.id ? null : order.id)}
                  returnRequest={latestReturnRequestForOrder(order.id)}
                  onRequestReturn={setReturnModalOrder}
                  onReorder={handleReorder}
                  reordering={reorderingOrderId === order.id}
                />
              ))}
            </div>
          )}

          {/* INVOICES */}
          {activeTab === "invoices" && (
            <div className="space-y-4">
              <h2 className="text-foreground" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem" }}>
                Rechnungen
              </h2>
              {invoicesLoading && (
                <p className="text-muted-foreground text-sm">Rechnungen werden geladen …</p>
              )}
              {invoicesError && (
                <p className="text-destructive text-sm">{invoicesError}</p>
              )}
              {!invoicesLoading && !invoicesError && invoices.length === 0 && (
                <p className="text-muted-foreground text-sm">Noch keine Rechnungen vorhanden.</p>
              )}
              {!invoicesLoading && !invoicesError && invoices.length > 0 && (
                <div className="bg-card border border-border rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border bg-muted/50">
                        <th className="text-left px-5 py-3 text-muted-foreground font-semibold" style={{ fontSize: "0.75rem", letterSpacing: "0.05em" }}>RECHNUNGSNR.</th>
                        <th className="text-left px-5 py-3 text-muted-foreground font-semibold hidden md:table-cell" style={{ fontSize: "0.75rem", letterSpacing: "0.05em" }}>DATUM</th>
                        <th className="text-right px-5 py-3 text-muted-foreground font-semibold" style={{ fontSize: "0.75rem", letterSpacing: "0.05em" }}>BETRAG</th>
                        <th className="px-5 py-3" />
                      </tr>
                    </thead>
                    <tbody>
                      {invoices.map((inv, idx) => (
                        <tr key={inv.id} className={`border-b border-border last:border-0 hover:bg-muted/30 transition-colors ${idx % 2 === 0 ? "" : "bg-muted/10"}`}>
                          <td className="px-5 py-3.5 font-mono text-foreground" style={{ fontSize: "0.83rem" }}>{inv.invoice_number}</td>
                          <td className="px-5 py-3.5 text-muted-foreground hidden md:table-cell" style={{ fontSize: "0.83rem" }}>{formatOrderDate(inv.issued_at)}</td>
                          <td className="px-5 py-3.5 text-right text-foreground font-semibold" style={{ fontFamily: "var(--font-display)", fontSize: "0.9rem" }}>
                            {Number(inv.total_amount).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                          </td>
                          <td className="px-5 py-3.5">
                            <button
                              onClick={() => handleDownloadInvoice(inv.id)}
                              disabled={downloadingInvoiceId === inv.id}
                              className="flex items-center gap-1 text-accent hover:text-accent/80 transition-colors text-xs font-semibold disabled:opacity-50"
                            >
                              <Download size={13} />
                              {downloadingInvoiceId === inv.id ? "Lädt …" : "PDF"}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* PERFORMANCE */}
          {activeTab === "performance" && (
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <h2 className="text-foreground" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem" }}>
                  PV-Leistung
                </h2>
                <DemoDataBadge />
              </div>
              <p className="text-muted-foreground text-xs">
                Diese Ansicht zeigt aktuell Beispieldaten – eine Anbindung an ein echtes
                PV-Monitoring-System ist derzeit nicht vorgesehen.
              </p>
              {/* System info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Installierte Leistung", value: "9,6 kWp", icon: Sun },
                  { label: "Heutiger Ertrag", value: "28,4 kWh", icon: Zap },
                  { label: "Jahresertrag", value: `${totalKwh.toLocaleString("de-DE")} kWh`, icon: TrendingUp },
                  { label: "CO₂ eingespart", value: "2.431 kg", icon: CheckCircle },
                ].map((s) => {
                  const Icon = s.icon;
                  return (
                    <div key={s.label} className="bg-card border border-border rounded-xl p-4 flex items-start gap-3">
                      <div className="w-9 h-9 rounded-lg bg-accent/15 flex items-center justify-center shrink-0">
                        <Icon size={18} className="text-accent" />
                      </div>
                      <div>
                        <div className="text-foreground font-bold" style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem" }}>{s.value}</div>
                        <div className="text-muted-foreground text-xs">{s.label}</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Today's output */}
              <div className="bg-card border border-border rounded-xl p-5">
                <h2 className="text-foreground mb-4" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem" }}>
                  Tagesleistung — 15. Juni 2025
                </h2>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={dailyData}>
                    <defs>
                      <linearGradient id="dayGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F5A623" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#F5A623" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                    <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#5A738A" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#5A738A" }} axisLine={false} tickLine={false} unit=" kW" />
                    <Tooltip
                      formatter={(v: number) => [`${v} kW`, "Leistung"]}
                      contentStyle={{ border: "1px solid rgba(0,0,0,0.1)", borderRadius: 6, fontSize: 12 }}
                    />
                    <Area type="monotone" dataKey="kw" stroke="#F5A623" strokeWidth={2.5} fill="url(#dayGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Monthly bar chart */}
              <div className="bg-card border border-border rounded-xl p-5">
                <h2 className="text-foreground mb-4" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem" }}>
                  Monatliche Erträge & Einsparungen
                </h2>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={pvMonthlyData} barGap={4}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" vertical={false} />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#5A738A" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#5A738A" }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ border: "1px solid rgba(0,0,0,0.1)", borderRadius: 6, fontSize: 12 }}
                    />
                    <Bar dataKey="kwh" name="Ertrag kWh" fill="#F5A623" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="eur" name="Einsparung €" fill="#0B2545" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex items-center gap-5 mt-3">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="w-3 h-3 rounded-sm bg-accent" />
                    Ertrag (kWh)
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="w-3 h-3 rounded-sm bg-primary" />
                    Einsparung (€)
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {returnModalOrder && (
        <ReturnRequestModal
          order={returnModalOrder}
          onClose={() => setReturnModalOrder(null)}
          onSubmitted={(returnRequest) =>
            setReturnRequests((current) => [returnRequest, ...current])
          }
        />
      )}
    </div>
  );
}

function OrderCard({
  order,
  expanded,
  onToggle,
  returnRequest,
  onRequestReturn,
  onReorder,
  reordering,
}: {
  order: ConfirmedOrder;
  expanded: boolean;
  onToggle: () => void;
  returnRequest?: ReturnRequest;
  onRequestReturn: (order: ConfirmedOrder) => void;
  onReorder: (order: ConfirmedOrder) => void;
  reordering: boolean;
}) {
  const status = paymentStatusConfig[order.payment_status as keyof typeof paymentStatusConfig] ?? paymentStatusConfig.pending;
  const statusLabel =
    ORDER_STATUS_LABELS[order.payment_status as keyof typeof ORDER_STATUS_LABELS] ?? order.payment_status;
  const StatusIcon = status.icon;
  const steps = buildOrderTimeline(order);
  const currentStep = steps.filter((s) => s.done).length - 1;
  const itemsSummary = order.items.map((entry) => `${entry.item_name} × ${entry.quantity}`).join(" + ");

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div
        className="flex flex-col sm:flex-row sm:items-center gap-3 px-5 py-4 cursor-pointer hover:bg-muted/20 transition-colors"
        onClick={onToggle}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-foreground font-mono font-semibold" style={{ fontSize: "0.85rem" }}>{order.order_number}</span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${status.bg} ${status.color}`}>
              <StatusIcon size={10} />
              {statusLabel}
            </span>
            {returnRequest && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border bg-blue-50 border-blue-200 text-blue-600">
                <RotateCcw size={10} />
                {RETURN_REQUEST_STATUS_LABELS[returnRequest.status]}
              </span>
            )}
          </div>
          <p className="text-muted-foreground text-xs truncate">{itemsSummary}</p>
          <p className="text-muted-foreground text-xs mt-0.5">{formatOrderDate(order.created_at)}</p>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-foreground font-bold text-right" style={{ fontFamily: "var(--font-display)", fontSize: "1.05rem" }}>
            {Number(order.total).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onReorder(order);
            }}
            disabled={reordering}
            className="flex items-center gap-1.5 text-accent hover:text-accent/80 transition-colors text-xs font-semibold disabled:opacity-50 shrink-0"
          >
            {reordering ? <Loader2 size={13} className="animate-spin" /> : <RotateCcw size={13} />}
            <span className="hidden sm:inline">Erneut bestellen</span>
          </button>
          <ChevronRight size={16} className={`text-muted-foreground transition-transform duration-200 ${expanded ? "rotate-90" : ""}`} />
        </div>
      </div>

      {expanded && (
        <div className="border-t border-border px-5 py-5 bg-muted/10">
          <h4 className="text-foreground mb-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Zahlungsstatus</h4>
          <div className="relative">
            {steps.map((step, idx) => {
              const isLast = idx === steps.length - 1;
              const isDone = step.done;
              const isCurrent = idx === currentStep + 1;
              return (
                <div key={step.label} className="flex items-start gap-4 relative">
                  {/* Line */}
                  {!isLast && (
                    <div className={`absolute left-[11px] top-6 w-0.5 h-full ${isDone ? "bg-green-400" : "bg-border"}`} style={{ height: "calc(100% - 1.5rem)" }} />
                  )}
                  {/* Dot */}
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 ${
                    isDone
                      ? "border-green-500 bg-green-500"
                      : isCurrent
                      ? "border-accent bg-accent/20"
                      : "border-border bg-card"
                  }`}>
                    {isDone && <CheckCircle size={12} className="text-white" />}
                    {isCurrent && <div className="w-2 h-2 rounded-full bg-accent" />}
                  </div>
                  {/* Content */}
                  <div className="pb-5">
                    <div className={`text-sm font-medium ${isDone ? "text-foreground" : isCurrent ? "text-accent" : "text-muted-foreground"}`}>
                      {step.label}
                    </div>
                    {step.date && <div className="text-muted-foreground text-xs mt-0.5">{step.date}</div>}
                  </div>
                </div>
              );
            })}
            {(order.payment_status === "failed" || order.payment_status === "cancelled") && (
              <p className="text-xs mt-1 flex items-center gap-1.5 text-red-600">
                <AlertCircle size={12} />
                {order.payment_status === "failed"
                  ? "Zahlung fehlgeschlagen."
                  : "Bestellung storniert."}
              </p>
            )}
          </div>

          {(order.can_request_return || returnRequest) && (
            <div className="mt-6 pt-5 border-t border-border">
              <h4 className="text-foreground mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Rückgabe / Widerruf
              </h4>
              {returnRequest ? (
                <div className="text-sm">
                  <p className="text-foreground font-medium mb-1">
                    {RETURN_REQUEST_STATUS_LABELS[returnRequest.status]}
                  </p>
                  <p className="text-muted-foreground text-xs">
                    Angefragt am {formatOrderDate(returnRequest.requested_at)}
                    {returnRequest.status === "rejected" && returnRequest.rejection_note
                      ? ` – ${returnRequest.rejection_note}`
                      : ""}
                  </p>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRequestReturn(order);
                  }}
                  className="flex items-center gap-1.5 text-accent hover:text-accent/80 transition-colors text-xs font-semibold"
                >
                  <RotateCcw size={13} />
                  Rückgabe anfragen
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
