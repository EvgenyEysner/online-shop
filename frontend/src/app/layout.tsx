import type { Metadata } from "next";
import "./globals.css";
import { AppProvider } from "@/src/providers/AppProvider";
import { RootShell } from "@/src/components/RootShell";

export const metadata: Metadata = {
  title: "KÖNIG39 – PV & Elektro Shop",
  description: "Ihr Fachhandel für Photovoltaik, Batteriespeicher und Elektroteile",
  manifest: "/manifest.json",
  themeColor: "#0B2545",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de" suppressHydrationWarning>
      <body>
        <AppProvider>
          <RootShell>{children}</RootShell>
        </AppProvider>
      </body>
    </html>
  );
}
