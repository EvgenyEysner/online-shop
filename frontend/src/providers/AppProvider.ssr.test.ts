// @vitest-environment node
import { describe, expect, it } from "vitest";
import { loadStoredCart } from "@/src/providers/AppProvider";

describe("loadStoredCart (SSR, window === undefined)", () => {
  it("gibt [] zurück und greift nicht auf window/localStorage zu", () => {
    expect(typeof window).toBe("undefined");
    expect(() => loadStoredCart()).not.toThrow();
    expect(loadStoredCart()).toEqual([]);
  });
});
