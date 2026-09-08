"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth-store";

export function useAuth() {
  const store = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => {
      setHydrated(true);
    });
    setHydrated(useAuthStore.persist.hasHydrated());
    return unsub;
  }, []);

  return { ...store, hydrated };
}
