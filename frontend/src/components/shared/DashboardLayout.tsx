"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { Sidebar } from "@/components/shared/Sidebar";
import { TopNav } from "@/components/shared/TopNav";
import { RoleSwitcher } from "@/components/shared/RoleSwitcher";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, hydrated, logout, setRole } = useAuth();

  useEffect(() => {
    if (hydrated && !user) {
      router.replace("/auth/login");
    }
  }, [hydrated, router, user]);

  if (!hydrated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="glass rounded-xl px-6 py-4 text-sm text-muted-foreground">
          Loading workspace…
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar role={user.role} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNav user={user} onRoleChange={setRole} onLogout={logout} />
        <main className="flex-1 p-4 pb-20 lg:p-8 lg:pb-24">{children}</main>
      </div>
      {/* Floating demo role switcher — always visible for demo purposes */}
      <RoleSwitcher />
    </div>
  );
}
