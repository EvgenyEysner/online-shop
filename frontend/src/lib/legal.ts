export interface LegalPage {
  slug: string;
  title: string;
  file: string;
}

export const LEGAL_PAGES: LegalPage[] = [
  { slug: "impressum", title: "Impressum", file: "impressum.md" },
  { slug: "agb", title: "AGB", file: "agb.md" },
  { slug: "datenschutz", title: "Datenschutz", file: "datenschutz.md" },
  { slug: "widerruf", title: "Widerrufsbelehrung", file: "widerruf.md" },
];

export function getLegalPage(slug: string): LegalPage | undefined {
  return LEGAL_PAGES.find((page) => page.slug === slug);
}

export interface CompanyInfo {
  name: string;
  street: string;
  zip: string;
  city: string;
  country: string;
  tax_id: string;
  email: string;
  phone: string;
  managing_director: string;
  register_court: string;
  register_number: string;
}

// Ersetzt Platzhalter wie {{company_name}} durch die passenden Werte aus dem
// CompanyInfoView-Response. Unbekannte Platzhalter bleiben unverändert
// stehen, damit fehlende Felder im Markdown auffallen statt lautlos zu
// verschwinden.
export function interpolate(template: string, company: CompanyInfo): string {
  const values: Record<string, string> = {
    company_name: company.name,
    company_street: company.street,
    company_zip: company.zip,
    company_city: company.city,
    company_country: company.country,
    company_tax_id: company.tax_id,
    company_email: company.email,
    company_phone: company.phone,
    company_managing_director: company.managing_director,
    company_register_court: company.register_court,
    company_register_number: company.register_number,
  };

  return template.replace(/{{\s*(\w+)\s*}}/g, (match, key: string) =>
    key in values ? values[key] : match
  );
}
