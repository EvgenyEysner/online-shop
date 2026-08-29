"use client";

import { useEffect } from "react";

export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

    // Finale Entscheidung (ADR 0005): nur in Production registrieren,
    // damit der Service Worker Next.js' Hot-Reload/Fast-Refresh in Dev
    // nicht durch gecachte Antworten stört.
    if (process.env.NODE_ENV !== "production") return;

    navigator.serviceWorker.register("/sw.js").catch((error) => {
      console.error("Service Worker Registrierung fehlgeschlagen:", error);
    });
  }, []);

  return null;
}
