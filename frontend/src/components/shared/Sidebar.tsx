"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Shield } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import { navSectionsForRole } from "@/lib/nav-config";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types/auth";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

function NavLinks({
  role,
  onNavigate,
}: {
  role: UserRole;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const sections = navSectionsForRole(role);

  return (
    <nav className="flex flex-1 flex-col gap-4 overflow-y-auto p-3">
      {sections.map(({ section, items }) => (
        <div key={section}>
          <p className="mb-1 px-3 py-1 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
            {section}
          </p>
          {items.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={`${item.href}-${item.label}`}
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  "group relative flex items-start gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-200",
                  active
                    ? "bg-white/10 text-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                )}
              >
                {/* Active left accent bar */}
                {active && (
                  <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-blue-400" />
                )}
                <Icon
                  className={cn(
                    "mt-0.5 h-4 w-4 shrink-0 transition-colors",
                    active ? "text-blue-400" : "text-zinc-500 group-hover:text-zinc-300",
                  )}
                />
                <span className="flex flex-col">
                  <span className="font-medium leading-tight">{item.label}</span>
                  <span className="text-[11px] text-muted-foreground group-hover:text-zinc-400">
                    {item.description}
                  </span>
                </span>
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

export function MobileSidebar({ role }: { role: UserRole }) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button variant="outline" size="icon" className="lg:hidden">
          <Menu className="h-4 w-4" />
          <span className="sr-only">Open navigation</span>
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="glass fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-white/10">
          <Dialog.Title className="sr-only">Navigation</Dialog.Title>
          <SidebarHeader />
          <Separator className="opacity-60" />
          <NavLinks role={role} onNavigate={() => setOpen(false)} />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function SidebarHeader() {
  return (
    <div className="flex items-center gap-3 px-5 py-5">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-500/30 bg-gradient-to-br from-blue-600/30 to-violet-600/20">
        <Shield className="h-5 w-5 text-blue-300" />
      </div>
      <div>
        <p className="text-sm font-semibold tracking-tight">RegTech AI</p>
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          Compliance OS
        </p>
      </div>
    </div>
  );
}

export function Sidebar({ role }: { role: UserRole }) {
  return (
    <aside className="glass hidden w-64 shrink-0 flex-col border-r border-white/10 lg:flex xl:w-72">
      <SidebarHeader />
      <Separator className="opacity-60" />
      <NavLinks role={role} />
      <div className="border-t border-white/5 p-4">
        <div className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
            Signed in as
          </p>
          <p className="mt-0.5 text-xs font-medium text-zinc-400">
            {role === "ADMIN"
              ? "System Administrator"
              : role === "REGULATOR"
                ? "Regulatory Authority"
                : "Organization Member"}
          </p>
        </div>
      </div>
    </aside>
  );
}
