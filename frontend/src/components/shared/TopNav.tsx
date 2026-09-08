"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import type { User, UserRole } from "@/types/auth";
import { MobileSidebar } from "@/components/shared/Sidebar";
import { useOrganizations } from "@/hooks/use-organizations";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const ROLE_LABEL: Record<UserRole, string> = {
  ADMIN: "Admin",
  REGULATOR: "Regulator",
  ORGANIZATION: "Organization",
};

function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function TopNav({
  user,
  onRoleChange,
  onLogout,
}: {
  user: User;
  onRoleChange: (role: UserRole) => void;
  onLogout: () => void;
}) {
  const router = useRouter();
  const { organizations, activeOrgId, setActiveOrg } = useOrganizations();
  const showOrgSelector =
    user.role === "ADMIN" || user.role === "REGULATOR";

  return (
    <header className="glass sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-white/10 px-4 lg:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <MobileSidebar role={user.role} />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">Control Center</p>
          <p className="truncate text-xs text-muted-foreground">
            AI-powered regulatory compliance
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {showOrgSelector && activeOrgId && (
          <Select value={activeOrgId} onValueChange={setActiveOrg}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Active organization" />
            </SelectTrigger>
            <SelectContent>
              {organizations.map((org) => (
                <SelectItem key={org.id} value={org.id}>
                  {org.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-11 gap-3 px-2">
              <Avatar>
                <AvatarFallback>{initials(user.name)}</AvatarFallback>
              </Avatar>
              <span className="hidden text-left sm:block">
                <span className="block text-sm font-medium leading-tight">
                  {user.name}
                </span>
                <span className="block text-xs text-muted-foreground">
                  {user.email}
                </span>
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel className="flex items-center justify-between gap-2 font-normal">
              <span>Signed in</span>
              <Badge variant="outline">{ROLE_LABEL[user.role]}</Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuLabel className="text-xs font-medium text-muted-foreground">
              Demo role
            </DropdownMenuLabel>
            <DropdownMenuRadioGroup
              value={user.role}
              onValueChange={(value) => onRoleChange(value as UserRole)}
            >
              {(Object.keys(ROLE_LABEL) as UserRole[]).map((role) => (
                <DropdownMenuRadioItem key={role} value={role}>
                  {ROLE_LABEL[role]}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onSelect={() => {
                onLogout();
                router.replace("/auth/login");
              }}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
