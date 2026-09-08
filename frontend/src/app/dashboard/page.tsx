"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  TrendingUp,
  FileStack,
  BookOpen,
  Upload,
  Search,
  Activity,
  ArrowRight,
  Zap,
} from "lucide-react";
import { navItemsForRole } from "@/lib/nav-config";
import { useAuth } from "@/hooks/use-auth";

const STAT_CARDS = [
  {
    label: "Regulations Indexed",
    value: "5",
    change: "+1 this week",
    icon: BookOpen,
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
  },
  {
    label: "Policy Documents",
    value: "4",
    change: "+2 this month",
    icon: FileStack,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
  },
  {
    label: "Compliance Checks",
    value: "127",
    change: "Last 30 days",
    icon: ShieldCheck,
    color: "text-violet-400",
    bg: "bg-violet-500/10 border-violet-500/20",
  },
  {
    label: "Avg Risk Score",
    value: "34",
    change: "↓ 8 vs last month",
    icon: TrendingUp,
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
  },
];

const QUICK_ACTIONS = [
  {
    label: "Run Compliance Check",
    description: "Analyse your policies against regulations",
    href: "/dashboard/compliance",
    icon: Search,
    gradient: "from-blue-600/80 to-violet-600/80",
    border: "border-blue-500/20",
    roles: ["ADMIN", "ORGANIZATION"],
  },
  {
    label: "Upload Regulation",
    description: "Ingest a new regulatory PDF",
    href: "/dashboard/regulations/upload",
    icon: Upload,
    gradient: "from-blue-600/60 to-cyan-600/60",
    border: "border-blue-500/20",
    roles: ["ADMIN", "REGULATOR"],
  },
  {
    label: "Upload Policy",
    description: "Add internal policy or SOP",
    href: "/dashboard/policies/upload",
    icon: Upload,
    gradient: "from-emerald-600/60 to-teal-600/60",
    border: "border-emerald-500/20",
    roles: ["ADMIN", "ORGANIZATION"],
  },
  {
    label: "System Health",
    description: "Check infrastructure status",
    href: "/dashboard/health",
    icon: Activity,
    gradient: "from-zinc-600/60 to-zinc-700/60",
    border: "border-zinc-500/20",
    roles: ["ADMIN"],
  },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const navItems = user ? navItemsForRole(user.role) : [];
  const quickActions = QUICK_ACTIONS.filter((a) =>
    user ? a.roles.includes(user.role) : false,
  );

  const roleLabel =
    user?.role === "ADMIN"
      ? "System Administrator"
      : user?.role === "REGULATOR"
        ? "Regulatory Authority"
        : "Organization Member";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="mx-auto max-w-5xl space-y-8"
    >
      {/* Welcome header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <Zap className="h-4 w-4 text-blue-400" />
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400">
              {roleLabel}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            Welcome back, {user?.name?.split(" ")[0] ?? "User"} 👋
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            AI-powered regulatory compliance platform. Here&apos;s your workspace overview.
          </p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {STAT_CARDS.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              className={`glass rounded-xl border p-4 ${stat.bg}`}
            >
              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs font-medium text-zinc-500">{stat.label}</p>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </div>
              <p className="text-2xl font-bold text-zinc-100">{stat.value}</p>
              <p className="mt-1 text-[11px] text-zinc-600">{stat.change}</p>
            </motion.div>
          );
        })}
      </div>

      {/* Quick actions */}
      {quickActions.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-zinc-400">
            Quick Actions
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {quickActions.map((action, i) => {
              const Icon = action.icon;
              return (
                <motion.div
                  key={action.href}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + i * 0.07 }}
                >
                  <Link
                    href={action.href}
                    className={`group flex items-center gap-4 rounded-xl border bg-gradient-to-r p-4 transition-all hover:brightness-110 ${action.gradient} ${action.border}`}
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/10">
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white">{action.label}</p>
                      <p className="text-xs text-white/60">{action.description}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-white/40 transition-transform group-hover:translate-x-1" />
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* All workspace items */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-zinc-400">
          Your Workspace
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {navItems.map((item, i) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={`${item.href}-${item.label}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.05 }}
              >
                <Link
                  href={item.href}
                  className="group glass flex items-start gap-3 rounded-xl p-4 transition-all hover:bg-white/[0.04]"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/8 bg-white/5 transition-colors group-hover:border-white/15">
                    <Icon className="h-4 w-4 text-zinc-400 group-hover:text-zinc-200" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100">
                      {item.label}
                    </p>
                    <p className="text-[11px] text-zinc-600">{item.description}</p>
                  </div>
                  <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-zinc-700 opacity-0 transition-all group-hover:opacity-100 group-hover:translate-x-0.5" />
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
