"use client";
import { useState } from "react";
import {
  ArrowLeft, CheckCircle, CreditCard, Building2, Smartphone,
  ChevronRight, MapPin, User, Phone, Mail, Package, Shield,
  Truck, FileText, Download, Home
} from "lucide-react";

interface CartItem {
  id: number;
  name: string;
  price: number;
  qty: number;
}

interface CheckoutProps {
  cart: CartItem[];
  onBack: () => void;
  onFinish: () => void;
}

type PaymentMethod = "bank" | "invoice" | "card" | "paypal";

const PAYMENT_METHODS: Array<{ key: PaymentMethod; label: string; desc: string; icon: React.ComponentType<{ size?: number; className?: string }> }> = [
  { key: "bank", label: "Überweisung", desc: "Zahlung per Banküberweisung (2–3 Werktage)", icon: Building2 },
  { key: "invoice", label: "Rechnung", desc: "Zahlung auf Rechnung (14 Tage Zahlungsziel)", icon: FileText },
  { key: "card", label: "Kreditkarte", desc: "Visa, Mastercard, American Express", icon: CreditCard },
  { key: "paypal", label: "PayPal", desc: "Schnell & sicher mit PayPal bezahlen", icon: Smartphone },
];

interface AddressForm {
  salutation: string;
  firstName: string;
  lastName: string;
  company: string;
  street: string;
  streetNo: string;
  zip: string;
  city: string;
  country: string;
  phone: string;
  email: string;
  notes: string;
  sameAsBilling: boolean;
}

const INITIAL_ADDRESS: AddressForm = {
  salutation: "Herr",
  firstName: "Max",
  lastName: "Mustermann",
  company: "",
  street: "Musterstraße",
  streetNo: "12",
  zip: "39104",
  city: "Magdeburg",
  country: "Deutschland",
  phone: "+49 391 123 456",
  email: "max@mustermann.de",
  notes: "",
  sameAsBilling: true,
};

const STEPS = [
  { key: "cart", label: "Warenkorb" },
  { key: "address", label: "Adresse" },
  { key: "payment", label: "Zahlung" },
  { key: "confirm", label: "Bestätigung" },
];

function StepIndicator({ current }: { current: string }) {
  const currentIdx = STEPS.findIndex(s => s.key === current);
  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {STEPS.map((step, idx) => {
        const isDone = idx < currentIdx;
        const isActive = idx === currentIdx;
        return (
          <div key={step.key} className="flex items-center">
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                isDone ? "bg-green-500 text-white" :
                isActive ? "bg-primary text-primary-foreground" :
                "bg-muted text-muted-foreground"
              }`}>
                {isDone ? <CheckCircle size={16} /> : idx + 1}
              </div>
              <span className={`text-xs mt-1 whitespace-nowrap hidden sm:block ${isActive ? "text-foreground font-semibold" : isDone ? "text-green-600" : "text-muted-foreground"}`}>
                {step.label}
              </span>
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`h-0.5 w-12 sm:w-20 mx-1 mt-[-1rem] sm:mt-[-1.5rem] transition-colors ${isDone ? "bg-green-400" : "bg-border"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function Checkout({ cart, onBack, onFinish }: CheckoutProps) {
  const [step, setStep] = useState<"cart" | "address" | "payment" | "confirm">("cart");
  const [address, setAddress] = useState<AddressForm>(INITIAL_ADDRESS);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("bank");
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [orderNumber] = useState(`K39-2025-${String(Math.floor(Math.random() * 900) + 100).padStart(4, "0")}`);

  const subtotal = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const shipping = subtotal >= 500 ? 0 : 4.90;
  const tax = (subtotal + shipping) * 0.19;
  const total = subtotal + shipping + tax;
  const totalGross = subtotal * 1.19 + shipping;

  const updateAddress = (field: keyof AddressForm, value: string | boolean) => {
    setAddress(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-primary text-white px-4 py-4 border-b border-white/10">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <button onClick={onBack} className="p-1.5 rounded hover:bg-white/10 transition-colors">
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.1rem" }}>Kasse</h1>
            <p className="text-white/50 text-xs">Sicherer Checkout — SSL-verschlüsselt</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5 text-white/40 text-xs">
            <Shield size={12} className="text-accent" />
            SSL-gesichert
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <StepIndicator current={step} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2">

            {/* STEP: Cart review */}
            {step === "cart" && (
              <div>
                <h2 className="text-foreground mb-5" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.2rem" }}>
                  Warenkorb prüfen
                </h2>
                <div className="space-y-3 mb-6">
                  {cart.map((item) => (
                    <div key={item.id} className="flex items-center gap-4 p-4 bg-card border border-border rounded-xl">
                      <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center shrink-0">
                        <Package size={20} className="text-muted-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-foreground text-sm font-semibold leading-snug">{item.name}</p>
                        <p className="text-muted-foreground text-xs mt-0.5">Menge: {item.qty}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-foreground font-bold" style={{ fontFamily: "var(--font-display)" }}>
                          {(item.price * item.qty * 1.19).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                        </p>
                        <p className="text-muted-foreground text-xs">{item.price.toLocaleString("de-DE", { style: "currency", currency: "EUR" })} / Stk.</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="p-4 bg-accent/10 border border-accent/20 rounded-xl flex items-center gap-3 mb-6">
                  <Truck size={16} className="text-accent shrink-0" />
                  <p className="text-foreground text-sm">
                    {shipping === 0
                      ? <><strong>Kostenlose Lieferung!</strong> Ab 500 € entfallen die Versandkosten.</>
                      : <>Versandkostenfrei ab 500,00 € — noch <strong>{(500 - subtotal).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}</strong> fehlen.</>
                    }
                  </p>
                </div>
                <button
                  onClick={() => setStep("address")}
                  className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Weiter zur Lieferadresse <ChevronRight size={16} />
                </button>
              </div>
            )}

            {/* STEP: Address */}
            {step === "address" && (
              <div>
                <h2 className="text-foreground mb-5" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.2rem" }}>
                  Lieferadresse
                </h2>
                <div className="space-y-4">
                  {/* Salutation */}
                  <div>
                    <label className="text-foreground text-sm font-semibold block mb-1.5">Anrede</label>
                    <div className="flex gap-2">
                      {["Herr", "Frau", "Divers"].map((s) => (
                        <button
                          key={s}
                          onClick={() => updateAddress("salutation", s)}
                          className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                            address.salutation === s
                              ? "border-primary bg-primary text-primary-foreground"
                              : "border-border bg-card text-foreground hover:border-primary/40"
                          }`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Name */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-foreground text-sm font-semibold block mb-1.5">Vorname *</label>
                      <input
                        value={address.firstName}
                        onChange={(e) => updateAddress("firstName", e.target.value)}
                        className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                      />
                    </div>
                    <div>
                      <label className="text-foreground text-sm font-semibold block mb-1.5">Nachname *</label>
                      <input
                        value={address.lastName}
                        onChange={(e) => updateAddress("lastName", e.target.value)}
                        className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                      />
                    </div>
                  </div>

                  {/* Company */}
                  <div>
                    <label className="text-foreground text-sm font-semibold block mb-1.5">Firma (optional)</label>
                    <input
                      placeholder="Firmenname"
                      value={address.company}
                      onChange={(e) => updateAddress("company", e.target.value)}
                      className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                    />
                  </div>

                  {/* Street */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="col-span-2">
                      <label className="text-foreground text-sm font-semibold block mb-1.5">Straße *</label>
                      <input
                        value={address.street}
                        onChange={(e) => updateAddress("street", e.target.value)}
                        className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                      />
                    </div>
                    <div>
                      <label className="text-foreground text-sm font-semibold block mb-1.5">Nr. *</label>
                      <input
                        value={address.streetNo}
                        onChange={(e) => updateAddress("streetNo", e.target.value)}
                        className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                      />
                    </div>
                  </div>

                  {/* ZIP + City */}
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-foreground text-sm font-semibold block mb-1.5">PLZ *</label>
                      <input
                        value={address.zip}
                        onChange={(e) => updateAddress("zip", e.target.value)}
                        className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="text-foreground text-sm font-semibold block mb-1.5">Ort *</label>
                      <input
                        value={address.city}
                        onChange={(e) => updateAddress("city", e.target.value)}
                        className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                      />
                    </div>
                  </div>

                  {/* Phone + Email */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-foreground text-sm font-semibold block mb-1.5">Telefon</label>
                      <div className="relative">
                        <Phone size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                        <input
                          value={address.phone}
                          onChange={(e) => updateAddress("phone", e.target.value)}
                          className="w-full pl-9 pr-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-foreground text-sm font-semibold block mb-1.5">E-Mail *</label>
                      <div className="relative">
                        <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                        <input
                          value={address.email}
                          onChange={(e) => updateAddress("email", e.target.value)}
                          className="w-full pl-9 pr-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Notes */}
                  <div>
                    <label className="text-foreground text-sm font-semibold block mb-1.5">Anmerkungen zur Bestellung</label>
                    <textarea
                      rows={2}
                      placeholder="z.B. Lieferhinweise, Wunschtermin…"
                      value={address.notes}
                      onChange={(e) => updateAddress("notes", e.target.value)}
                      className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40 resize-none"
                    />
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setStep("cart")}
                    className="px-5 py-2.5 border border-border text-foreground rounded-xl text-sm hover:bg-muted transition-colors"
                  >
                    Zurück
                  </button>
                  <button
                    onClick={() => setStep("payment")}
                    className="flex-1 py-2.5 bg-primary text-primary-foreground font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    Weiter zur Zahlung <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP: Payment */}
            {step === "payment" && (
              <div>
                <h2 className="text-foreground mb-5" style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.2rem" }}>
                  Zahlungsart wählen
                </h2>
                <div className="space-y-3 mb-6">
                  {PAYMENT_METHODS.map((pm) => {
                    const Icon = pm.icon;
                    const isSelected = paymentMethod === pm.key;
                    return (
                      <button
                        key={pm.key}
                        onClick={() => setPaymentMethod(pm.key)}
                        className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 text-left transition-all ${
                          isSelected
                            ? "border-primary bg-primary/5"
                            : "border-border bg-card hover:border-primary/30"
                        }`}
                      >
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
                          <Icon size={18} />
                        </div>
                        <div className="flex-1">
                          <p className={`text-sm font-bold ${isSelected ? "text-primary" : "text-foreground"}`}>{pm.label}</p>
                          <p className="text-muted-foreground text-xs mt-0.5">{pm.desc}</p>
                        </div>
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ${isSelected ? "border-primary" : "border-border"}`}>
                          {isSelected && <div className="w-2.5 h-2.5 rounded-full bg-primary" />}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Bank transfer details */}
                {paymentMethod === "bank" && (
                  <div className="p-4 bg-muted/50 border border-border rounded-xl mb-6 text-sm">
                    <p className="font-semibold text-foreground mb-2 flex items-center gap-2"><Building2 size={14} className="text-accent" /> Bankverbindung</p>
                    <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
                      <span className="text-muted-foreground">Empfänger</span><span className="text-foreground font-medium">König 39 GmbH</span>
                      <span className="text-muted-foreground">IBAN</span><span className="text-foreground font-mono font-medium">DE89 8100 0000 0123 4567 89</span>
                      <span className="text-muted-foreground">BIC</span><span className="text-foreground font-mono font-medium">BELADEBEXXX</span>
                      <span className="text-muted-foreground">Verwendungszweck</span><span className="text-foreground font-medium">Wird nach Bestellung mitgeteilt</span>
                    </div>
                  </div>
                )}

                {/* Card form */}
                {paymentMethod === "card" && (
                  <div className="p-4 bg-muted/50 border border-border rounded-xl mb-6 space-y-3">
                    <div>
                      <label className="text-foreground text-xs font-semibold block mb-1">Kartennummer</label>
                      <input placeholder="0000 0000 0000 0000" className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40 font-mono" />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-foreground text-xs font-semibold block mb-1">Gültig bis</label>
                        <input placeholder="MM/JJ" className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40 font-mono" />
                      </div>
                      <div>
                        <label className="text-foreground text-xs font-semibold block mb-1">CVC</label>
                        <input placeholder="123" className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40 font-mono" />
                      </div>
                    </div>
                  </div>
                )}

                {/* Terms */}
                <label className="flex items-start gap-3 cursor-pointer mb-6 p-4 bg-muted/30 border border-border rounded-xl">
                  <input
                    type="checkbox"
                    checked={agreeTerms}
                    onChange={(e) => setAgreeTerms(e.target.checked)}
                    className="mt-0.5 accent-[#0B2545]"
                  />
                  <span className="text-sm text-foreground leading-relaxed">
                    Ich habe die <a href="#" className="text-accent underline">AGB</a> und die <a href="#" className="text-accent underline">Datenschutzerklärung</a> gelesen und akzeptiere diese. Ich stimme dem Kauf zu.
                  </span>
                </label>

                <div className="flex gap-3">
                  <button
                    onClick={() => setStep("address")}
                    className="px-5 py-2.5 border border-border text-foreground rounded-xl text-sm hover:bg-muted transition-colors"
                  >
                    Zurück
                  </button>
                  <button
                    disabled={!agreeTerms}
                    onClick={() => setStep("confirm")}
                    className={`flex-1 py-2.5 font-bold rounded-xl flex items-center justify-center gap-2 transition-all ${
                      agreeTerms
                        ? "bg-accent text-primary hover:bg-accent/90"
                        : "bg-muted text-muted-foreground cursor-not-allowed"
                    }`}
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    <Shield size={16} />
                    Jetzt kostenpflichtig bestellen
                  </button>
                </div>
              </div>
            )}

            {/* STEP: Confirmation */}
            {step === "confirm" && (
              <div className="text-center">
                <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-5">
                  <CheckCircle size={40} className="text-green-500" />
                </div>
                <h2 className="text-foreground mb-2" style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: "1.5rem" }}>
                  Vielen Dank für Ihre Bestellung!
                </h2>
                <p className="text-muted-foreground mb-1">
                  Ihre Bestellnummer: <span className="text-foreground font-mono font-bold">{orderNumber}</span>
                </p>
                <p className="text-muted-foreground text-sm mb-8">
                  Eine Bestätigungs-E-Mail wurde an <strong>{address.email}</strong> gesendet.
                </p>

                {/* Order summary */}
                <div className="bg-card border border-border rounded-xl p-5 text-left mb-6">
                  <h3 className="text-foreground mb-3" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>Bestellübersicht</h3>
                  {cart.map((item) => (
                    <div key={item.id} className="flex justify-between py-2 border-b border-border last:border-0">
                      <span className="text-foreground text-sm">{item.name} × {item.qty}</span>
                      <span className="text-foreground text-sm font-semibold">{(item.price * item.qty * 1.19).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}</span>
                    </div>
                  ))}
                  <div className="flex justify-between pt-3 mt-1">
                    <span className="text-foreground font-bold" style={{ fontFamily: "var(--font-display)" }}>Gesamt</span>
                    <span className="text-foreground font-bold" style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem" }}>
                      {totalGross.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                    </span>
                  </div>
                </div>

                {/* Delivery address */}
                <div className="bg-card border border-border rounded-xl p-5 text-left mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <MapPin size={16} className="text-accent" />
                    <h3 className="text-foreground" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>Lieferadresse</h3>
                  </div>
                  <p className="text-foreground text-sm">{address.salutation} {address.firstName} {address.lastName}</p>
                  {address.company && <p className="text-foreground text-sm">{address.company}</p>}
                  <p className="text-muted-foreground text-sm">{address.street} {address.streetNo}, {address.zip} {address.city}</p>
                  <p className="text-muted-foreground text-sm">{address.country}</p>
                </div>

                {/* Payment */}
                <div className="bg-card border border-border rounded-xl p-5 text-left mb-8">
                  <div className="flex items-center gap-2 mb-2">
                    <CreditCard size={16} className="text-accent" />
                    <h3 className="text-foreground" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>Zahlungsart</h3>
                  </div>
                  <p className="text-foreground text-sm">{PAYMENT_METHODS.find(m => m.key === paymentMethod)?.label}</p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <button className="flex items-center justify-center gap-2 px-6 py-2.5 border border-border text-foreground rounded-xl text-sm hover:bg-muted transition-colors">
                    <Download size={15} /> Rechnung herunterladen
                  </button>
                  <button
                    onClick={onFinish}
                    className="flex items-center justify-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground font-bold rounded-xl text-sm hover:bg-primary/90 transition-colors"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    <Home size={15} /> Zurück zum Shop
                  </button>
                </div>

                {/* Next steps */}
                <div className="mt-8 p-5 bg-accent/10 border border-accent/20 rounded-xl text-left">
                  <h3 className="text-foreground mb-3" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>Nächste Schritte</h3>
                  <div className="space-y-2">
                    {[
                      { icon: Mail, text: "Sie erhalten eine Bestellbestätigung per E-Mail" },
                      { icon: Package, text: "Wir bereiten Ihre Bestellung vor (1–2 Werktage)" },
                      { icon: Truck, text: "Lieferung an Ihre Adresse in 3–5 Werktagen" },
                      { icon: User, text: "Bei Installationswunsch kontaktiert Sie unser Team" },
                    ].map((s, i) => {
                      const Icon = s.icon;
                      return (
                        <div key={i} className="flex items-center gap-3 text-sm text-muted-foreground">
                          <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center shrink-0">
                            <Icon size={12} className="text-accent" />
                          </div>
                          {s.text}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Order summary sidebar */}
          {step !== "confirm" && (
            <div className="lg:col-span-1">
              <div className="bg-card border border-border rounded-xl p-5 sticky top-24">
                <h3 className="text-foreground mb-4" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>Zusammenfassung</h3>
                <div className="space-y-2 mb-4">
                  {cart.map((item) => (
                    <div key={item.id} className="flex justify-between text-xs">
                      <span className="text-muted-foreground flex-1 min-w-0 mr-2 truncate">{item.name} ×{item.qty}</span>
                      <span className="text-foreground font-medium shrink-0">
                        {(item.price * item.qty).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="border-t border-border pt-3 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Zwischensumme (netto)</span>
                    <span className="text-foreground">{subtotal.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">MwSt. (19 %)</span>
                    <span className="text-foreground">{(subtotal * 0.19).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Versand</span>
                    <span className={shipping === 0 ? "text-green-600 font-semibold" : "text-foreground"}>
                      {shipping === 0 ? "Kostenlos" : shipping.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                    </span>
                  </div>
                  <div className="flex justify-between font-bold border-t border-border pt-2 mt-2">
                    <span className="text-foreground" style={{ fontFamily: "var(--font-display)" }}>Gesamtbetrag</span>
                    <span className="text-foreground" style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem" }}>
                      {totalGross.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                    </span>
                  </div>
                  <p className="text-muted-foreground text-xs">inkl. MwSt.</p>
                </div>

                {/* Trust */}
                <div className="mt-4 pt-4 border-t border-border space-y-2">
                  {[
                    { icon: Shield, text: "SSL-verschlüsselt & sicher" },
                    { icon: Truck, text: "Versand in 1–2 Werktagen" },
                    { icon: CheckCircle, text: "14 Tage Rückgaberecht" },
                  ].map((t) => {
                    const Icon = t.icon;
                    return (
                      <div key={t.text} className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Icon size={12} className="text-accent shrink-0" />
                        {t.text}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
