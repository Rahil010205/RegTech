"use client";

import React from "react";
import { Sparkles } from "lucide-react";

export function DemoBadge() {
  const isDemo = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

  if (!isDemo) return null;

  return (
    <div className="flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400 shadow-sm animate-pulse">
      <Sparkles className="h-3.5 w-3.5 text-amber-400" />
      <span>Demo Mode</span>
    </div>
  );
}
