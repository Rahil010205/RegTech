"use client";

import { useOrgStore } from "@/store/org-store";

export function useOrganizations() {
  const organizations = useOrgStore((s) => s.organizations);
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);
  const activeOrganization =
    organizations.find((org) => org.id === activeOrgId) ?? null;

  return { organizations, activeOrgId, activeOrganization, setActiveOrg };
}
