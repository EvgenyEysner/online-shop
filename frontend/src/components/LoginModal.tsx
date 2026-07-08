"use client";

import { useState } from "react";
import { X, Sun } from "lucide-react";

interface LoginModalProps {
  onClose: () => void;
  onLogin: () => void;
}

export function LoginModal({ onClose, onLogin }: LoginModalProps) {
  const [email, setEmail] = useState("max@mustermann.de");
  const [password, setPassword] = useState("password");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-2xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
              <Sun size={15} className="text-accent" />
            </div>
            <div>
              <div
                className="text-foreground font-bold leading-none"
                style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem" }}
              >
                KÖNIG<span className="text-accent">39</span>
              </div>
              <div className="text-muted-foreground leading-none" style={{ fontSize: "0.6rem" }}>
                Kundenanmeldung
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="text-foreground text-sm font-semibold block mb-1.5">
              E-Mail-Adresse
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
            />
          </div>
          <div>
            <label className="text-foreground text-sm font-semibold block mb-1.5">
              Passwort
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
            />
          </div>
          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 text-muted-foreground cursor-pointer">
              <input type="checkbox" className="rounded border-border" defaultChecked />
              Angemeldet bleiben
            </label>
            <a href="#" className="text-accent hover:underline">
              Passwort vergessen?
            </a>
          </div>
          <button
            onClick={onLogin}
            className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-lg hover:bg-primary/90 transition-colors"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Anmelden
          </button>
          <p className="text-center text-muted-foreground text-xs">
            Noch kein Konto?{" "}
            <a href="#" className="text-accent font-semibold hover:underline">
              Registrieren
            </a>
          </p>
          <div className="p-3 bg-muted/50 rounded-lg border border-border text-xs text-muted-foreground text-center">
            Demo: Daten bereits vorausgefüllt — einfach anmelden
          </div>
        </div>
      </div>
    </div>
  );
}
