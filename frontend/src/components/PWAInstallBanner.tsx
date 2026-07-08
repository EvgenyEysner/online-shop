"use client";

import { useState, useEffect } from "react";
import { X, Sun, Download } from "lucide-react";

export function PWAInstallBanner() {
  const [installPrompt, setInstallPrompt] = useState<Event | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Detect standalone/installed mode
    if (
      window.matchMedia("(display-mode: standalone)").matches ||
      (navigator as Navigator & { standalone?: boolean }).standalone
    ) {
      setIsInstalled(true);
      return;
    }

    const handler = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e);
    };
    window.addEventListener("beforeinstallprompt", handler);

    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  useEffect(() => {
    if (installPrompt && !isInstalled) {
      const t = setTimeout(() => setShowBanner(true), 5000);
      return () => clearTimeout(t);
    }
  }, [installPrompt, isInstalled]);

  const handleInstall = () => {
    if (!installPrompt) return;
    (installPrompt as BeforeInstallPromptEvent).prompt();
    setShowBanner(false);
  };

  if (!showBanner || isInstalled) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:w-80 z-40 bg-primary text-white rounded-xl shadow-2xl p-4 border border-white/10">
      <button
        onClick={() => setShowBanner(false)}
        className="absolute top-3 right-3 text-white/40 hover:text-white"
      >
        <X size={16} />
      </button>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center shrink-0">
          <Sun size={18} className="text-primary" />
        </div>
        <div>
          <p
            className="text-white font-bold text-sm"
            style={{ fontFamily: "var(--font-display)" }}
          >
            App installieren
          </p>
          <p className="text-white/60 text-xs mt-0.5 mb-3">
            Installieren Sie König 39 für schnelleren Zugriff auf Ihrem Gerät.
          </p>
          <button
            onClick={handleInstall}
            className="flex items-center gap-2 px-3 py-1.5 bg-accent text-primary text-xs font-bold rounded-lg"
          >
            <Download size={12} /> Jetzt installieren
          </button>
        </div>
      </div>
    </div>
  );
}

// Extend BeforeInstallPromptEvent type
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}
