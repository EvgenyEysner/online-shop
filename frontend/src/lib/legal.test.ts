import { describe, expect, it } from "vitest";
import {
  getLegalPage,
  interpolate,
  LEGAL_PAGES,
  type CompanyInfo,
} from "@/src/lib/legal";

const company: CompanyInfo = {
  name: "König 39 Solar & Elektro",
  street: "Musterstraße 39",
  zip: "39104",
  city: "Magdeburg",
  country: "Deutschland",
  tax_id: "DE000000000",
  email: "info@koenig39.de",
  phone: "+49 391 000",
  managing_director: "Max Beispiel",
  register_court: "Amtsgericht Magdeburg",
  register_number: "HRB 00000",
};

describe("LEGAL_PAGES / getLegalPage", () => {
  it("kennt die vier Pflichtseiten", () => {
    expect(LEGAL_PAGES.map((page) => page.slug)).toEqual([
      "impressum",
      "agb",
      "datenschutz",
      "widerruf",
    ]);
  });

  it("liefert undefined für unbekannte Slugs", () => {
    expect(getLegalPage("does-not-exist")).toBeUndefined();
  });
});

describe("interpolate", () => {
  it("ersetzt bekannte Firmen-Platzhalter", () => {
    const result = interpolate(
      "{{company_name}} · {{company_zip}} {{company_city}}",
      company
    );

    expect(result).toBe("König 39 Solar & Elektro · 39104 Magdeburg");
  });

  it("lässt unbekannte Platzhalter unverändert stehen", () => {
    expect(interpolate("Hallo {{unknown_field}}", company)).toBe(
      "Hallo {{unknown_field}}"
    );
  });

  it("toleriert Leerzeichen in den Klammern", () => {
    expect(interpolate("{{ company_email }}", company)).toBe("info@koenig39.de");
  });
});
