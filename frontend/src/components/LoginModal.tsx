"use client";

import { FormEvent, useState } from "react";
import { Loader2, X, Sun } from "lucide-react";
import { ApiError } from "@/src/lib/api";

interface LoginModalProps {
  onClose: () => void;
  onLogin: (
    email: string,
    password: string,
    rememberMe: boolean
  ) => Promise<void>;
}

export function LoginModal({ onClose, onLogin }: LoginModalProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await onLogin(email.trim(), password, rememberMe);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Anmeldung fehlgeschlagen. Bitte versuchen Sie es erneut.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

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
            type="button"
            onClick={onClose}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground"
            disabled={isSubmitting}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label
              htmlFor="login-email"
              className="text-foreground text-sm font-semibold block mb-1.5"
            >
              E-Mail-Adresse
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={isSubmitting}
              className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60"
            />
          </div>
          <div>
            <label
              htmlFor="login-password"
              className="text-foreground text-sm font-semibold block mb-1.5"
            >
              Passwort
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              disabled={isSubmitting}
              className="w-full px-3 py-2.5 bg-input-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60"
            />
          </div>
          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                className="rounded border-border"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isSubmitting}
              />
              Angemeldet bleiben
            </label>
            <a href="#" className="text-accent hover:underline">
              Passwort vergessen?
            </a>
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Anmeldung läuft…
              </>
            ) : (
              "Anmelden"
            )}
          </button>
          <p className="text-center text-muted-foreground text-xs">
            Noch kein Konto?{" "}
            <a href="#" className="text-accent font-semibold hover:underline">
              Registrieren
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
