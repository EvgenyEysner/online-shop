"use client";
import { Sun, Phone, Mail, MapPin, Facebook, Instagram, Linkedin } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-primary text-white">
      <div className="max-w-7xl mx-auto px-4 pt-12 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-9 h-9 rounded bg-accent flex items-center justify-center">
                <Sun size={18} className="text-primary" />
              </div>
              <div>
                <div className="text-white font-bold" style={{ fontFamily: "var(--font-display)", fontSize: "1.05rem" }}>
                  KÖNIG<span className="text-accent">39</span>
                </div>
                <div className="text-white/40" style={{ fontSize: "0.55rem", letterSpacing: "0.12em" }}>SOLAR & ELEKTRO</div>
              </div>
            </div>
            <p className="text-white/50 text-xs leading-relaxed mb-4">
              Ihr zuverlässiger Partner für Solaranlagen und Elektroinstallationen in Sachsen-Anhalt. Qualität und Erfahrung seit 2017.
            </p>
            <div className="flex gap-2">
              {[Facebook, Instagram, Linkedin].map((Icon, i) => (
                <button key={i} className="w-8 h-8 rounded bg-white/10 hover:bg-accent/20 hover:text-accent flex items-center justify-center transition-colors text-white/60">
                  <Icon size={14} />
                </button>
              ))}
            </div>
          </div>

          {/* Shop */}
          <div>
            <h4 className="text-white mb-4 text-sm font-semibold" style={{ fontFamily: "var(--font-display)" }}>Shop</h4>
            <ul className="space-y-2">
              {["PV-Anlagen", "Wechselrichter", "Batteriespeicher", "Elektroteile", "Kabel & Leitungen", "Zubehör"].map((item) => (
                <li key={item}>
                  <a href="#" className="text-white/50 text-xs hover:text-accent transition-colors">{item}</a>
                </li>
              ))}
            </ul>
          </div>

          {/* Service */}
          <div>
            <h4 className="text-white mb-4 text-sm font-semibold" style={{ fontFamily: "var(--font-display)" }}>Service</h4>
            <ul className="space-y-2">
              {["Installation", "Wartung & Reparatur", "Netzanmeldung", "Energieberatung", "Fördermittel", "Garantieleistungen"].map((item) => (
                <li key={item}>
                  <a href="#" className="text-white/50 text-xs hover:text-accent transition-colors">{item}</a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white mb-4 text-sm font-semibold" style={{ fontFamily: "var(--font-display)" }}>Kontakt</h4>
            <ul className="space-y-3">
              <li className="flex items-start gap-2">
                <MapPin size={13} className="text-accent mt-0.5 shrink-0" />
                <span className="text-white/50 text-xs leading-relaxed">Musterstraße 39<br />39104 Magdeburg</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone size={13} className="text-accent shrink-0" />
                <a href="tel:+493912345678" className="text-white/50 text-xs hover:text-accent transition-colors">+49 391 234 56 78</a>
              </li>
              <li className="flex items-center gap-2">
                <Mail size={13} className="text-accent shrink-0" />
                <a href="mailto:info@koenig39.de" className="text-white/50 text-xs hover:text-accent transition-colors">info@koenig39.de</a>
              </li>
            </ul>
            <div className="mt-4 p-3 bg-white/5 rounded-lg border border-white/10">
              <div className="text-white text-xs font-semibold mb-1" style={{ fontFamily: "var(--font-display)" }}>Öffnungszeiten</div>
              <div className="text-white/50 text-xs">Mo–Fr: 08:00–17:00 Uhr</div>
              <div className="text-white/50 text-xs">Sa: nach Vereinbarung</div>
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 pt-6 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="text-white/30 text-xs">© 2025 König 39 GmbH. Alle Rechte vorbehalten.</p>
          <div className="flex gap-4">
            {["Impressum", "Datenschutz", "AGB", "Widerruf"].map((link) => (
              <a key={link} href="#" className="text-white/30 text-xs hover:text-accent/70 transition-colors">{link}</a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
