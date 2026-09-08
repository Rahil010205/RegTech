"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import type { UserRole } from "@/types/auth";
import { useAuth } from "@/hooks/use-auth";

export function RoleGuard({
  allow,
  children,
}: {
  allow: UserRole[];
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, hydrated } = useAuth();

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      router.replace("/auth/login");
      return;
    }
    if (!allow.includes(user.role)) {
      router.replace("/dashboard");
    }
  }, [allow, hydrated, router, user]);

  if (!hydrated || !user || !allow.includes(user.role)) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
        Checking access…
      </div>
    );
  }

  return <>{children}</>;
}
