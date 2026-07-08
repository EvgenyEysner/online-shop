"use client";

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import type { ProductDetailData } from "@/src/components/ProductDetail";

export interface CartItem {
  id: number;
  name: string;
  price: number;
  qty: number;
}

interface AppContextValue {
  // Cart
  cart: CartItem[];
  cartCount: number;
  addToCart: (product: ProductDetailData, qty?: number) => void;
  removeFromCart: (id: number) => void;
  clearCart: () => void;

  // Cart drawer
  showCart: boolean;
  openCart: () => void;
  closeCart: () => void;

  // Auth
  isLoggedIn: boolean;
  login: () => void;
  logout: () => void;

  // Login modal
  showLogin: boolean;
  openLogin: () => void;
  closeLogin: () => void;

  // Selected product (for /product/[id] route)
  selectedProduct: ProductDetailData | null;
  setSelectedProduct: (p: ProductDetailData | null) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [showCart, setShowCart] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [selectedProduct, setSelectedProduct] =
    useState<ProductDetailData | null>(null);

  const cartCount = cart.reduce((s, i) => s + i.qty, 0);

  const addToCart = (product: ProductDetailData, qty = 1) => {
    setCart((prev) => {
      const existing = prev.find((i) => i.id === product.id);
      if (existing)
        return prev.map((i) =>
          i.id === product.id ? { ...i, qty: i.qty + qty } : i
        );
      return [...prev, { id: product.id, name: product.name, price: product.price, qty }];
    });
  };

  const removeFromCart = (id: number) =>
    setCart((prev) => prev.filter((i) => i.id !== id));

  const clearCart = () => setCart([]);

  const login = () => { setIsLoggedIn(true); setShowLogin(false); };
  const logout = () => setIsLoggedIn(false);

  return (
    <AppContext.Provider
      value={{
        cart,
        cartCount,
        addToCart,
        removeFromCart,
        clearCart,
        showCart,
        openCart: () => setShowCart(true),
        closeCart: () => setShowCart(false),
        isLoggedIn,
        login,
        logout,
        showLogin,
        openLogin: () => setShowLogin(true),
        closeLogin: () => setShowLogin(false),
        selectedProduct,
        setSelectedProduct,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  // During SSR the context may not be initialized yet — return a safe no-op
  // fallback so the server render doesn't crash. Hydration fixes it client-side.
  if (!ctx) {
    return {
      cart: [] as CartItem[],
      cartCount: 0,
      addToCart: () => {},
      removeFromCart: () => {},
      clearCart: () => {},
      showCart: false,
      openCart: () => {},
      closeCart: () => {},
      isLoggedIn: false,
      login: () => {},
      logout: () => {},
      showLogin: false,
      openLogin: () => {},
      closeLogin: () => {},
      selectedProduct: null,
      setSelectedProduct: () => {},
    } satisfies AppContextValue;
  }
  return ctx;
}
