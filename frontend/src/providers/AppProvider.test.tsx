import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  AppProvider,
  isValidCartItem,
  loadStoredCart,
  useApp,
  type CartItem,
} from "@/src/providers/AppProvider";
import type { CatalogProduct } from "@/src/types/catalog";

vi.mock("@/src/lib/auth", () => ({
  fetchCurrentUser: vi.fn().mockRejectedValue(new Error("nicht angemeldet")),
  clearTokens: vi.fn(),
  storeTokens: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
}));

const CART_STORAGE_KEY = "k39_cart_v1";

function makeProduct(overrides: Partial<CatalogProduct> = {}): CatalogProduct {
  return {
    id: 1,
    name: "Solarmodul",
    description: "",
    price: 199.99,
    rating: 5,
    reviews: 0,
    category: "solar",
    image: "",
    specs: [],
    ...overrides,
  };
}

function TestConsumer() {
  const { cart, cartCount, addToCart, removeFromCart, clearCart } = useApp();
  return (
    <div>
      <span data-testid="cart-count">{cartCount}</span>
      <span data-testid="cart-length">{cart.length}</span>
      <button onClick={() => addToCart(makeProduct(), 2)}>add</button>
      <button onClick={() => addToCart(makeProduct(), 5000)}>add-huge</button>
      <button onClick={() => removeFromCart(1)}>remove</button>
      <button onClick={() => clearCart()}>clear</button>
    </div>
  );
}

describe("loadStoredCart", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("gibt [] zurück, wenn localStorage unter k39_cart_v1 nichts enthält", () => {
    expect(loadStoredCart()).toEqual([]);
  });

  it("gibt [] zurück und wirft nicht, wenn der gespeicherte Wert kein valides JSON ist", () => {
    localStorage.setItem(CART_STORAGE_KEY, "{invalid");

    expect(() => loadStoredCart()).not.toThrow();
    expect(loadStoredCart()).toEqual([]);
  });

  it("verwirft ungültige Einträge und behält gültige Einträge im selben Array", () => {
    const valid: CartItem = { id: 1, name: "Solarmodul", price: 199.99, qty: 2 };
    const invalidEntries = [
      { id: "not-a-number", name: "x", price: 1, qty: 1 },
      { name: "missing id", price: 1, qty: 1 },
      { id: 2, name: "invalid qty null", price: 1, qty: 0 },
      { id: 3, name: "invalid qty negativ", price: 1, qty: -1 },
      "not-an-object",
    ];
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify([valid, ...invalidEntries]));

    expect(loadStoredCart()).toEqual([valid]);
  });

  it("verwirft einen manipulierten localStorage-Eintrag mit qty: Infinity (ADR 0008, Finding 4)", () => {
    const valid: CartItem = { id: 1, name: "Solarmodul", price: 199.99, qty: 2 };
    const corrupted = { id: 9, name: "Manipuliert", price: 1, qty: Infinity };
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify([valid, corrupted]));

    expect(loadStoredCart()).toEqual([valid]);
  });

  it("verwirft einen manipulierten localStorage-Eintrag mit qty über der Obergrenze 999 (ADR 0008, Finding 4)", () => {
    const valid: CartItem = { id: 1, name: "Solarmodul", price: 199.99, qty: 2 };
    const corrupted = { id: 9, name: "Manipuliert", price: 1, qty: 1000 };
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify([valid, corrupted]));

    expect(loadStoredCart()).toEqual([valid]);
  });
});

describe("isValidCartItem", () => {
  it("akzeptiert ein valides CartItem", () => {
    expect(isValidCartItem({ id: 1, name: "x", price: 1, qty: 1 })).toBe(true);
  });

  it("akzeptiert die Obergrenze von 999 selbst", () => {
    expect(isValidCartItem({ id: 1, name: "x", price: 1, qty: 999 })).toBe(true);
  });

  it.each([
    [null],
    [undefined],
    ["string"],
    [{ id: "1", name: "x", price: 1, qty: 1 }],
    [{ id: 1, name: "x", price: 1, qty: 0 }],
    [{ id: 1, name: "x", price: 1, qty: -5 }],
    [{ name: "x", price: 1, qty: 1 }],
  ])("lehnt ungültigen Wert ab: %j", (value) => {
    expect(isValidCartItem(value)).toBe(false);
  });

  // ADR 0008, Finding 4: Infinity ist ein gültiger JS `number`-Wert und
  // besteht `typeof entry.qty === "number"` sowie (für +Infinity) auch
  // `entry.qty > 0` - Number.isFinite() muss das explizit abfangen. NaN
  // wird bereits durch die bestehende `> 0`-Prüfung abgedeckt
  // (NaN > 0 === false), ist hier zur Dokumentation trotzdem mit aufgeführt.
  it.each([
    [Infinity],
    [-Infinity],
    [NaN],
    [1000],
    [Number.MAX_SAFE_INTEGER],
  ])("lehnt qty=%p ab (Endlichkeits-/Obergrenzen-Prüfung)", (qty) => {
    expect(isValidCartItem({ id: 1, name: "x", price: 1, qty })).toBe(false);
  });
});

describe("AppProvider Cart-Persistenz (Integration)", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("stellt einen zuvor gespeicherten Cart nach dem ersten Effect wieder her", async () => {
    const stored: CartItem[] = [{ id: 5, name: "Wechselrichter", price: 500, qty: 3 }];
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(stored));

    render(
      <AppProvider>
        <TestConsumer />
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("cart-count").textContent).toBe("3");
    });
  });

  it("persistiert addToCart in localStorage unter k39_cart_v1", async () => {
    const user = userEvent.setup();
    render(
      <AppProvider>
        <TestConsumer />
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("cart-length").textContent).toBe("0");
    });

    await user.click(screen.getByText("add"));

    await waitFor(() => {
      const raw = localStorage.getItem(CART_STORAGE_KEY);
      expect(raw).not.toBeNull();
      expect(JSON.parse(raw as string)).toEqual([
        { id: 1, name: "Solarmodul", price: 199.99, qty: 2 },
      ]);
    });
  });

  it("persistiert removeFromCart und clearCart in localStorage", async () => {
    const user = userEvent.setup();
    const stored: CartItem[] = [{ id: 1, name: "Solarmodul", price: 199.99, qty: 2 }];
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(stored));

    render(
      <AppProvider>
        <TestConsumer />
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("cart-length").textContent).toBe("1");
    });

    await user.click(screen.getByText("remove"));

    await waitFor(() => {
      expect(JSON.parse(localStorage.getItem(CART_STORAGE_KEY) as string)).toEqual([]);
    });

    await user.click(screen.getByText("add"));

    await waitFor(() => {
      expect(screen.getByTestId("cart-length").textContent).toBe("1");
    });

    await user.click(screen.getByText("clear"));

    await waitFor(() => {
      expect(JSON.parse(localStorage.getItem(CART_STORAGE_KEY) as string)).toEqual([]);
    });
  });

  it("erhöht addToCart die Menge eines bestehenden Items nicht über die Obergrenze 999 (ADR 0008, Finding 4)", async () => {
    const user = userEvent.setup();
    const stored: CartItem[] = [
      { id: 1, name: "Solarmodul", price: 199.99, qty: 998 },
    ];
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(stored));

    render(
      <AppProvider>
        <TestConsumer />
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("cart-count").textContent).toBe("998");
    });

    // TestConsumer's "add"-Button ruft addToCart(product-id-1, qty=2) auf -
    // 998 + 2 = 1000 würde ohne Clamp die Obergrenze überschreiten.
    await user.click(screen.getByText("add"));

    await waitFor(() => {
      expect(screen.getByTestId("cart-count").textContent).toBe("999");
    });

    const raw = localStorage.getItem(CART_STORAGE_KEY);
    expect(JSON.parse(raw as string)).toEqual([
      { id: 1, name: "Solarmodul", price: 199.99, qty: 999 },
    ]);
  });

  it("clamped addToCart die Menge auch bei einem komplett neuen Produkt auf die Obergrenze 999 (ADR 0008, Finding 4)", async () => {
    const user = userEvent.setup();
    render(
      <AppProvider>
        <TestConsumer />
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("cart-length").textContent).toBe("0");
    });

    // TestConsumer's "add-huge"-Button ruft addToCart(product-id-1, qty=5000)
    // auf einem leeren Cart auf - ohne Clamp würde qty: 5000 gespeichert.
    await user.click(screen.getByText("add-huge"));

    await waitFor(() => {
      expect(screen.getByTestId("cart-count").textContent).toBe("999");
    });

    const raw = localStorage.getItem(CART_STORAGE_KEY);
    expect(JSON.parse(raw as string)).toEqual([
      { id: 1, name: "Solarmodul", price: 199.99, qty: 999 },
    ]);
  });
});
