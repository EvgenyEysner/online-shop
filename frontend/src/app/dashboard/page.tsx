"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/src/providers/AppProvider";
import { CustomerDashboard } from "@/src/components/CustomerDashboard";

export default function DashboardPage() {
  const router = useRouter();
  const { logout, isLoggedIn, authLoading, openLogin } = useApp();

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      openLogin();
      router.replace("/");
    }
  }, [authLoading, isLoggedIn, openLogin, router]);

  if (authLoading || !isLoggedIn) {
    return null;
  }

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return <CustomerDashboard onLogout={handleLogout} />;
}
