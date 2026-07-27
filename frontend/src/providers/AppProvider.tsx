"use client";

import {createContext, type ReactNode, useCallback, useContext, useEffect, useState,} from "react";
import type {CatalogProduct} from "@/src/types/catalog";
import {
    clearTokens,
    fetchCurrentUser,
    login as loginRequest,
    register as registerRequest,
    storeTokens,
} from "@/src/lib/auth";
import type {User} from "@/src/types/user";

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
    addToCart: (product: CatalogProduct, qty?: number) => void;
    removeFromCart: (id: number) => void;
    clearCart: () => void;

    // Cart drawer
    showCart: boolean;
    openCart: () => void;
    closeCart: () => void;

    // Auth
    user: User | null;
    isLoggedIn: boolean;
    authLoading: boolean;
    login: (
        email: string,
        password: string,
        rememberMe?: boolean
    ) => Promise<void>;

    signUp: (
        email: string,
        firstName: string,
        lastName: string,
        password: string,
        passwordConfirm: string,
    ) => Promise<void>;

    logout: () => void;

    // Login modal
    showLogin: boolean;
    openLogin: () => void;
    closeLogin: () => void;

    // Selected product (for /product/[id] route)
    selectedProduct: CatalogProduct | null;
    setSelectedProduct: (p: CatalogProduct | null) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({children}: { children: ReactNode }) {
    const [cart, setCart] = useState<CartItem[]>([]);
    const [showCart, setShowCart] = useState(false);
    const [user, setUser] = useState<User | null>(null);
    const [authLoading, setAuthLoading] = useState(true);
    const [showLogin, setShowLogin] = useState(false);
    const [selectedProduct, setSelectedProduct] =
        useState<CatalogProduct | null>(null);

    const cartCount = cart.reduce((s, i) => s + i.qty, 0);
    const isLoggedIn = user !== null;

    useEffect(() => {
        let cancelled = false;

        async function restoreSession() {
            try {
                const currentUser = await fetchCurrentUser();
                if (!cancelled) setUser(currentUser);
            } catch {
                if (!cancelled) {
                    clearTokens();
                    setUser(null);
                }
            } finally {
                if (!cancelled) setAuthLoading(false);
            }
        }

        restoreSession();
        return () => {
            cancelled = true;
        };
    }, []);

    const addToCart = (product: CatalogProduct, qty = 1) => {
        setCart((prev) => {
            const existing = prev.find((i) => i.id === product.id);
            if (existing)
                return prev.map((i) =>
                    i.id === product.id ? {...i, qty: i.qty + qty} : i
                );
            return [...prev, {id: product.id, name: product.name, price: product.price, qty}];
        });
    };

    const removeFromCart = (id: number) =>
        setCart((prev) => prev.filter((i) => i.id !== id));

    const clearCart = () => setCart([]);

    const signUp = useCallback(
        async (
            email: string,
            firstName: string,
            lastName: string,
            password: string,
            passwordConfirm: string
        ) => {
            const tokens = await registerRequest(
                email,
                firstName,
                lastName,
                password,
                passwordConfirm
            );
            storeTokens(tokens, true);
            const currentUser = await fetchCurrentUser(tokens.access);
            setUser(currentUser);
            setShowLogin(false);
        },
        []
    );

    const login = useCallback(
        async (email: string, password: string, rememberMe = true) => {
            const tokens = await loginRequest(email, password);
            storeTokens(tokens, rememberMe);
            const currentUser = await fetchCurrentUser(tokens.access);
            setUser(currentUser);
            setShowLogin(false);
        },
        []
    );

    const logout = useCallback(() => {
        clearTokens();
        setUser(null);
    }, []);

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
                user,
                isLoggedIn,
                authLoading,
                signUp,
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
            addToCart: () => {
            },
            removeFromCart: () => {
            },
            clearCart: () => {
            },
            showCart: false,
            openCart: () => {
            },
            closeCart: () => {
            },
            user: null,
            isLoggedIn: false,
            authLoading: true,
            signUp: async () => {
            },
            login: async () => {
            },
            logout: () => {
            },
            showLogin: false,
            openLogin: () => {
            },
            closeLogin: () => {
            },
            selectedProduct: null,
            setSelectedProduct: () => {
            },
        } satisfies AppContextValue;
    }
    return ctx;
}
