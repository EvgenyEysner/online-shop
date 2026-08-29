import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { ServiceWorkerRegistration } from "@/src/components/ServiceWorkerRegistration";

function stubServiceWorker(register: (url: string) => Promise<unknown>) {
  Object.defineProperty(navigator, "serviceWorker", {
    value: { register },
    configurable: true,
  });
}

function removeServiceWorker() {
  if ("serviceWorker" in navigator) {
    delete (navigator as unknown as Record<string, unknown>).serviceWorker;
  }
}

describe("ServiceWorkerRegistration", () => {
  afterEach(() => {
    removeServiceWorker();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("registriert den Service Worker in production, wenn serviceWorker unterstützt wird", () => {
    vi.stubEnv("NODE_ENV", "production");
    const registerMock = vi.fn().mockResolvedValue(undefined);
    stubServiceWorker(registerMock);

    render(<ServiceWorkerRegistration />);

    expect(registerMock).toHaveBeenCalledTimes(1);
    expect(registerMock).toHaveBeenCalledWith("/sw.js");
  });

  it("registriert NICHT, wenn NODE_ENV nicht 'production' ist", () => {
    vi.stubEnv("NODE_ENV", "test");
    const registerMock = vi.fn().mockResolvedValue(undefined);
    stubServiceWorker(registerMock);

    render(<ServiceWorkerRegistration />);

    expect(registerMock).not.toHaveBeenCalled();
  });

  it("registriert nicht und wirft nicht, wenn 'serviceWorker' nicht in navigator existiert", () => {
    vi.stubEnv("NODE_ENV", "production");
    removeServiceWorker();

    expect(() => render(<ServiceWorkerRegistration />)).not.toThrow();
  });

  it("ruft console.error auf, wenn register() rejected, ohne unbehandelten Fehler zu werfen", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const error = new Error("Registrierung fehlgeschlagen");
    const registerMock = vi.fn().mockRejectedValue(error);
    stubServiceWorker(registerMock);
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(<ServiceWorkerRegistration />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Service Worker Registrierung fehlgeschlagen:",
        error
      );
    });
  });
});
