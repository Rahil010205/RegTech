import { useEffect } from "react";
import { useOrgStore } from "@/store/org-store";

export function useOrganizations() {
  const organizations = useOrgStore((s) => s.organizations);
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);
  const loadOrganizations = useOrgStore((s) => s.loadOrganizations);
  const createOrganization = useOrgStore((s) => s.createOrganization);

  const activeOrganization =
    organizations.find((org) => org.id === activeOrgId) ?? null;

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  return {
    organizations,
    activeOrgId,
    activeOrganization,
    setActiveOrg,
    loadOrganizations,
    createOrganization,
  };
}
