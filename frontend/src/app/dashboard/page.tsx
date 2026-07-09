"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/src/providers/AppProvider";
import { CustomerDashboard } from "@/src/components/CustomerDashboard";

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, isLoggedIn, authLoading, openLogin } = useApp();

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      openLogin();
      router.replace("/");
    }
  }, [authLoading, isLoggedIn, openLogin, router]);

  if (authLoading || !isLoggedIn || !user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return <CustomerDashboard user={user} onLogout={handleLogout} />;
}
