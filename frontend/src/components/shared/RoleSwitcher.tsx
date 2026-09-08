"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/hooks/use-auth";
import type { UserRole } from "@/types/auth";
import { cn } from "@/lib/utils";

const ROLES: { role: UserRole; label: string; color: string; bg: string }[] = [
  {
    role: "ADMIN",
    label: "Admin",
    color: "text-violet-300",
    bg: "bg-violet-500/20 hover:bg-violet-500/30 border-violet-500/40",
  },
  {
    role: "REGULATOR",
    label: "Regulator",
    color: "text-blue-300",
    bg: "bg-blue-500/20 hover:bg-blue-500/30 border-blue-500/40",
  },
  {
    role: "ORGANIZATION",
    label: "Org",
    color: "text-emerald-300",
    bg: "bg-emerald-500/20 hover:bg-emerald-500/30 border-emerald-500/40",
  },
];

export function RoleSwitcher() {
  const { user, setRole } = useAuth();

  if (!user) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5, type: "spring", stiffness: 300, damping: 30 }}
        className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2"
        id="role-switcher"
      >
        <div className="flex items-center gap-1 rounded-full border border-white/10 bg-zinc-950/80 px-2 py-1.5 shadow-2xl backdrop-blur-xl">
          <span className="pl-2 pr-1 text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
            Demo Role
          </span>
          <div className="mx-1.5 h-3 w-px bg-white/10" />
          {ROLES.map(({ role, label, color, bg }) => (
            <button
              key={role}
              id={`role-btn-${role.toLowerCase()}`}
              onClick={() => setRole(role)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-semibold transition-all duration-200",
                color,
                bg,
                user.role === role
                  ? "ring-1 ring-white/20 shadow-lg scale-105"
                  : "opacity-60 hover:opacity-100",
              )}
            >
              {label}
              {user.role === role && (
                <motion.span
                  layoutId="active-role-dot"
                  className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current"
                />
              )}
            </button>
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
