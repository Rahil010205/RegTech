"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface RiskBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

type RiskLevel = "low" | "medium" | "high";

function getRiskLevel(score: number): RiskLevel {
  if (score < 20) return "low";
  if (score <= 70) return "medium";
  return "high";
}

const RISK_CONFIG: Record<
  RiskLevel,
  {
    label: string;
    textColor: string;
    bgColor: string;
    borderColor: string;
    ringColor: string;
    glowColor: string;
  }
> = {
  low: {
    label: "Low Risk",
    textColor: "text-emerald-300",
    bgColor: "bg-emerald-500/15",
    borderColor: "border-emerald-500/40",
    ringColor: "ring-emerald-400/30",
    glowColor: "shadow-emerald-500/20",
  },
  medium: {
    label: "Medium Risk",
    textColor: "text-amber-300",
    bgColor: "bg-amber-500/15",
    borderColor: "border-amber-500/40",
    ringColor: "ring-amber-400/30",
    glowColor: "shadow-amber-500/20",
  },
  high: {
    label: "High Risk",
    textColor: "text-red-300",
    bgColor: "bg-red-500/15",
    borderColor: "border-red-500/40",
    ringColor: "ring-red-400/30",
    glowColor: "shadow-red-500/20",
  },
};

const SIZE_CONFIG = {
  sm: { badge: "px-2 py-0.5 text-[10px]", score: "text-sm", dot: "h-1.5 w-1.5" },
  md: { badge: "px-3 py-1 text-xs", score: "text-base", dot: "h-2 w-2" },
  lg: { badge: "px-4 py-1.5 text-sm", score: "text-xl font-bold", dot: "h-2.5 w-2.5" },
};

export function RiskBadge({
  score,
  size = "md",
  showLabel = true,
  className,
}: RiskBadgeProps) {
  const level = getRiskLevel(score);
  const config = RISK_CONFIG[level];
  const sizeConfig = SIZE_CONFIG[size];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-semibold shadow-lg",
        config.bgColor,
        config.borderColor,
        config.textColor,
        config.glowColor,
        sizeConfig.badge,
        className,
      )}
    >
      {/* Pulsing dot */}
      <span className="relative flex items-center justify-center">
        <motion.span
          animate={{ scale: [1, 1.8, 1], opacity: [0.6, 0, 0.6] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className={cn(
            "absolute rounded-full bg-current",
            sizeConfig.dot,
          )}
        />
        <span
          className={cn("rounded-full bg-current", sizeConfig.dot)}
        />
      </span>

      {/* Score */}
      <span className={sizeConfig.score}>{score}</span>

      {/* Label */}
      {showLabel && (
        <span className="opacity-80">{config.label}</span>
      )}
    </motion.div>
  );
}

// Compact score-only variant for table cells
export function RiskScoreCell({ score }: { score: number }) {
  const level = getRiskLevel(score);
  const config = RISK_CONFIG[level];

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ delay: 0.2, duration: 0.8, ease: "easeOut" }}
          className={cn(
            "h-full rounded-full",
            level === "low"
              ? "bg-emerald-400"
              : level === "medium"
                ? "bg-amber-400"
                : "bg-red-400",
          )}
        />
      </div>
      <span
        className={cn("text-xs font-semibold tabular-nums", config.textColor)}
      >
        {score}
      </span>
    </div>
  );
}
