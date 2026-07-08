"use client";

import { useRouter } from "next/navigation";
import { useApp } from "@/src/providers/AppProvider";
import { CustomerDashboard } from "@/src/components/CustomerDashboard";

export default function DashboardPage() {
  const router = useRouter();
  const { logout, isLoggedIn, openLogin } = useApp();

  // Redirect unauthenticated users
  if (!isLoggedIn) {
    openLogin();
    router.replace("/");
    return null;
  }

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return <CustomerDashboard onLogout={handleLogout} />;
}
