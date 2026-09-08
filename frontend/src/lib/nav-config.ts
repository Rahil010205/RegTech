import {
  BookOpen,
  Building2,
  FileStack,
  ShieldCheck,
  Users,
  Upload,
  Search,
  BarChart3,
  Activity,
  type LucideIcon,
} from "lucide-react";
import type { UserRole } from "@/types/auth";

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
  roles: UserRole[];
  section: string;
}

export const NAV_ITEMS: NavItem[] = [
  // ── ADMIN ─────────────────────────────────────────────────────────────────
  {
    href: "/dashboard/health",
    label: "System Health",
    description: "API, DB, and service status",
    icon: Activity,
    roles: ["ADMIN"],
    section: "System",
  },
  {
    href: "/dashboard/regulations",
    label: "All Regulations",
    description: "Browse and manage regulatory corpora",
    icon: BookOpen,
    roles: ["ADMIN"],
    section: "Regulations",
  },
  {
    href: "/dashboard/org-profiles",
    label: "All Organizations",
    description: "Inspect registered organization profiles",
    icon: Building2,
    roles: ["ADMIN"],
    section: "Organizations",
  },
  {
    href: "/dashboard/policies",
    label: "All Policies",
    description: "Browse organization policy documents",
    icon: FileStack,
    roles: ["ADMIN"],
    section: "Policies",
  },
  {
    href: "/dashboard/compliance",
    label: "Compliance Analysis",
    description: "Run evaluations and review risk scores",
    icon: ShieldCheck,
    roles: ["ADMIN"],
    section: "Compliance",
  },
  {
    href: "/dashboard/users",
    label: "User Management",
    description: "Provision users and assign roles",
    icon: Users,
    roles: ["ADMIN"],
    section: "System",
  },

  // ── REGULATOR ─────────────────────────────────────────────────────────────
  {
    href: "/dashboard/regulations",
    label: "Regulatory Library",
    description: "Browse and manage regulatory corpora",
    icon: BookOpen,
    roles: ["REGULATOR"],
    section: "Regulations",
  },
  {
    href: "/dashboard/regulations/upload",
    label: "Upload Regulation",
    description: "Ingest a new regulatory PDF",
    icon: Upload,
    roles: ["REGULATOR"],
    section: "Regulations",
  },
  {
    href: "/dashboard/org-profiles",
    label: "Org Analytics",
    description: "View compliance status across organizations",
    icon: BarChart3,
    roles: ["REGULATOR"],
    section: "Analytics",
  },

  // ── ORGANIZATION ──────────────────────────────────────────────────────────
  {
    href: "/dashboard/policies",
    label: "My Policies",
    description: "Manage internal policy documents",
    icon: FileStack,
    roles: ["ORGANIZATION"],
    section: "Policies",
  },
  {
    href: "/dashboard/policies/upload",
    label: "Upload Policy",
    description: "Add a new internal policy or SOP",
    icon: Upload,
    roles: ["ORGANIZATION"],
    section: "Policies",
  },
  {
    href: "/dashboard/compliance",
    label: "Compliance Search",
    description: "Semantic search against regulations",
    icon: Search,
    roles: ["ORGANIZATION"],
    section: "Compliance",
  },
  {
    href: "/dashboard/regulations",
    label: "Regulation Library",
    description: "Browse applicable regulations",
    icon: BookOpen,
    roles: ["ORGANIZATION"],
    section: "Regulations",
  },
];

export function navItemsForRole(role: UserRole): NavItem[] {
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}

export function navSectionsForRole(
  role: UserRole,
): { section: string; items: NavItem[] }[] {
  const items = navItemsForRole(role);
  const sectionMap = new Map<string, NavItem[]>();

  for (const item of items) {
    if (!sectionMap.has(item.section)) {
      sectionMap.set(item.section, []);
    }
    sectionMap.get(item.section)!.push(item);
  }

  return Array.from(sectionMap.entries()).map(([section, items]) => ({
    section,
    items,
  }));
}
