import React, { useState } from "react";
import { useOrganizations } from "@/hooks/use-organizations";
import { OrganizationCreateModal } from "./OrganizationCreateModal";
import { Plus } from "lucide-react";

export function OrganizationSelector() {
  const { organizations, activeOrgId, setActiveOrg } = useOrganizations();
  const [showCreate, setShowCreate] = useState(false);

  return (
    <div className="flex items-center gap-2">
      <select
        value={activeOrgId ?? ""}
        onChange={(e) => setActiveOrg(e.target.value)}
        className="rounded-lg border border-white/10 bg-zinc-900/90 px-3 py-2 text-sm text-zinc-200 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 outline-none"
        aria-label="Select organization"
      >
        <option value="" disabled className="bg-zinc-900 text-zinc-500">
          -- Select Organization --
        </option>
        {organizations.map((org) => (
          <option key={org.id} value={org.id} className="bg-zinc-900 text-zinc-100">
            {org.name}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={() => setShowCreate(true)}
        className="flex items-center gap-1 rounded-lg bg-emerald-600 px-2.5 py-2 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors"
        title="Create new organization"
        aria-label="Create organization"
      >
        <Plus className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">New</span>
      </button>
      {showCreate && <OrganizationCreateModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

