import { promises as fs } from "fs";
import http from "http";
import https from "https";
import path from "path";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ReactMarkdown, { type Components } from "react-markdown";
import { getApiBaseUrl } from "@/src/lib/api";
import {
  getLegalPage,
  interpolate,
  LEGAL_PAGES,
  type CompanyInfo,
} from "@/src/lib/legal";

interface LegalPageRouteProps {
  params: Promise<{ slug: string }>;
}

const markdownComponents: Components = {
  h1: ({ children }) => (
    <h2
      className="text-xl font-semibold text-foreground mt-2 mb-4"
      style={{ fontFamily: "var(--font-display)" }}
    >
      {children}
    </h2>
  ),
  h2: ({ children }) => (
    <h3
      className="text-lg font-semibold text-foreground mt-8 mb-3"
      style={{ fontFamily: "var(--font-display)" }}
    >
      {children}
    </h3>
  ),
  h3: ({ children }) => (
    <h4 className="text-base font-semibold text-foreground mt-6 mb-2">
      {children}
    </h4>
  ),
  p: ({ children }) => (
    <p className="text-muted-foreground text-sm leading-relaxed mb-4">
      {children}
    </p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-5 space-y-1.5 text-muted-foreground text-sm mb-4">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-5 space-y-1.5 text-muted-foreground text-sm mb-4">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  a: ({ children, href }) => (
    <a href={href} className="text-accent hover:underline">
      {children}
    </a>
  ),
  strong: ({ children }) => (
    <strong className="text-foreground font-semibold">{children}</strong>
  ),
  hr: () => <hr className="border-border my-6" />,
};

// Nutzt bewusst Node's http/https statt der globalen fetch()-Funktion: Next.js
// patcht fetch() mit einer eigenen Cache-/Memoisierungsschicht, die für
// Firmenstammdaten (Impressum-Pflichtangaben) nie stale Ergebnisse liefern
// darf. Der rohe Node-Client umgeht diese Schicht vollständig.
function fetchCompanyInfo(): Promise<CompanyInfo> {
  const url = new URL(`${getApiBaseUrl()}/api/v1/core/company/`);
  const client = url.protocol === "https:" ? https : http;

  return new Promise((resolve, reject) => {
    const request = client.get(url, (response) => {
      const status = response.statusCode ?? 0;
      const chunks: Buffer[] = [];

      response.on("data", (chunk: Buffer) => chunks.push(chunk));
      response.on("end", () => {
        if (status < 200 || status >= 300) {
          reject(
            new Error(`Firmendaten konnten nicht geladen werden (Status ${status}).`)
          );
          return;
        }

        try {
          resolve(JSON.parse(Buffer.concat(chunks).toString("utf-8")) as CompanyInfo);
        } catch (error) {
          reject(error);
        }
      });
    });

    request.on("error", reject);
  });
}

// Bewusst KEIN generateStaticParams(): Firmendaten (Impressum-Pflichtangaben)
// und Rechtstexte dürfen nie aus einem veralteten Cache/Build-Snapshot
// ausgeliefert werden - jede Anfrage rendert frisch gegen die aktuellen
// COMPANY_*-Settings. generateStaticParams würde diese vier Seiten beim
// `next build` vorrendern (inkl. eines Build-Zeit-Requests an das Backend,
// das zum Build-Zeitpunkt ggf. nicht erreichbar ist) und stünde damit im
// Widerspruch zu `force-dynamic` unten.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function generateMetadata({
  params,
}: LegalPageRouteProps): Promise<Metadata> {
  const { slug } = await params;
  const page = getLegalPage(slug);

  return { title: page ? `${page.title} – KÖNIG39` : "Nicht gefunden" };
}

export default async function LegalPageRoute({ params }: LegalPageRouteProps) {
  const { slug } = await params;
  const page = getLegalPage(slug);

  if (!page) {
    notFound();
  }

  const filePath = path.join(process.cwd(), "content", "legal", page.file);
  const [template, company] = await Promise.all([
    fs.readFile(filePath, "utf-8"),
    fetchCompanyInfo(),
  ]);

  const content = interpolate(template, company);

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1
        className="text-2xl font-bold text-foreground mb-8"
        style={{ fontFamily: "var(--font-display)" }}
      >
        {page.title}
      </h1>
      <div className="bg-card border border-border rounded-2xl p-6 md:p-8">
        <ReactMarkdown components={markdownComponents}>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
